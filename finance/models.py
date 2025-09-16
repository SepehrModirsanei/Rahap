from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta


class User(AbstractUser):
    # Extend later if needed
    pass


class Wallet(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    currency = models.CharField(max_length=10, default='IRR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet({self.user.username}) {self.balance} {self.currency}"


class Account(models.Model):
    ACCOUNT_TYPE_RIAL = 'rial'
    ACCOUNT_TYPE_GOLD = 'gold'
    ACCOUNT_TYPE_FOREIGN = 'foreign'
    ACCOUNT_TYPE_CURRENCY = 'currency'
    ACCOUNT_TYPE_CHOICES = [
        (ACCOUNT_TYPE_RIAL, 'Rial'),
        (ACCOUNT_TYPE_GOLD, 'Gold'),
        (ACCOUNT_TYPE_FOREIGN, 'Foreign'),
        (ACCOUNT_TYPE_CURRENCY, 'Currency'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts')
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    initial_balance = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    # e.g., 2.5 => 2.5% monthly
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            # capture initial balance on first save
            self.initial_balance = Decimal(self.balance)
        super().save(*args, **kwargs)

    def accrue_monthly_profit(self):
        now = timezone.now()
        if not self.monthly_profit_rate:
            return
        # Compute profit based on daily snapshots over last 30 days ending yesterday
        period_end = date.today()
        period_start = period_end - timedelta(days=30)
        snapshots = list(self.daily_balances.filter(snapshot_date__gt=period_start).order_by('snapshot_date'))
        # Get carry snapshot on or before start
        carry = self.daily_balances.filter(snapshot_date__lte=period_start).order_by('-snapshot_date').first()
        segments = []
        # Build segments between dates with constant balance
        prev_date = period_start
        prev_balance = Decimal(carry.balance) if carry else Decimal(self.balance)
        for snap in snapshots:
            d = snap.snapshot_date
            if d > prev_date:
                segments.append((prev_date, d, Decimal(snap.balance) if False else prev_balance))
            prev_date = d
            prev_balance = Decimal(snap.balance)
        # Last segment until period_end
        if prev_date < period_end:
            segments.append((prev_date, period_end, prev_balance))
        # Sum daily balances
        total_days = Decimal(0)
        weighted_sum = Decimal(0)
        for start, end, bal in segments:
            days = Decimal((end - start).days)
            if days > 0:
                total_days += days
                weighted_sum += (bal * days)
        if total_days == 0:
            return
        # Monthly profit = rate% * (sum of daily balances / 30)
        average_balance = weighted_sum / Decimal(30)
        profit = (average_balance * Decimal(self.monthly_profit_rate)) / Decimal(100)
        if profit <= 0:
            return
        self.balance += profit
        self.last_profit_accrual_at = now
        self.save(update_fields=['balance', 'last_profit_accrual_at', 'updated_at'])
        Transaction.objects.create(
            user=self.user,
            source_account=None,
            destination_account=self,
            source_wallet=None,
            destination_wallet=None,
            amount=profit,
            kind=Transaction.KIND_PROFIT_ACCOUNT,
        )

    def __str__(self):
        return f"Account({self.user.username}:{self.name}:{self.account_type})"


class Deposit(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='deposits')
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    # Profit goes to wallet (not compounded)
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure wallet belongs to user and has enough balance on creation
        from django.core.exceptions import ValidationError
        if self.wallet and self.user and self.wallet.user_id != self.user_id:
            raise ValidationError('Wallet must belong to the same user as the deposit.')
        # On create only (no PK yet), require sufficient funds
        if not self.pk and self.wallet and self.amount is not None:
            if Decimal(self.wallet.balance) < Decimal(self.amount):
                raise ValidationError('Insufficient wallet balance for initial deposit amount.')

    def accrue_monthly_profit(self):
        now = timezone.now()
        if self.monthly_profit_rate and (not self.last_profit_accrual_at or (now - self.last_profit_accrual_at).days >= 28):
            profit = (self.amount * self.monthly_profit_rate) / 100
            # credit wallet
            self.wallet.balance += profit
            self.wallet.save(update_fields=['balance', 'updated_at'])
            self.last_profit_accrual_at = now
            self.save(update_fields=['last_profit_accrual_at', 'updated_at'])
            Transaction.objects.create(
                user=self.user,
                source_account=None,
                destination_account=None,
                source_wallet=None,
                destination_wallet=self.wallet,
                amount=profit,
                kind=Transaction.KIND_PROFIT_DEPOSIT_TO_WALLET,
            )

    def __str__(self):
        return f"Deposit({self.user.username}) amount={self.amount}"


class Transaction(models.Model):
    KIND_ADD_TO_WALLET = 'add_to_wallet'
    KIND_REMOVE_FROM_WALLET = 'remove_from_wallet'
    KIND_TRANSFER_ACCOUNT_TO_WALLET = 'account_to_wallet'
    KIND_TRANSFER_WALLET_TO_ACCOUNT = 'wallet_to_account'
    KIND_TRANSFER_WALLET_TO_WALLET = 'wallet_to_wallet'
    KIND_TRANSFER_ACCOUNT_TO_ACCOUNT = 'account_to_account'
    KIND_WALLET_TO_DEPOSIT_INITIAL = 'wallet_to_deposit_initial'
    KIND_PROFIT_ACCOUNT = 'profit_account'
    KIND_PROFIT_DEPOSIT_TO_WALLET = 'profit_deposit_wallet'

    KIND_CHOICES = [
        (KIND_ADD_TO_WALLET, 'Add to Wallet'),
        (KIND_REMOVE_FROM_WALLET, 'Remove from Wallet'),
        (KIND_TRANSFER_ACCOUNT_TO_WALLET, 'Account to Wallet'),
        (KIND_TRANSFER_WALLET_TO_ACCOUNT, 'Wallet to Account'),
        (KIND_TRANSFER_WALLET_TO_WALLET, 'Wallet to Wallet'),
        (KIND_TRANSFER_ACCOUNT_TO_ACCOUNT, 'Account to Account'),
        (KIND_WALLET_TO_DEPOSIT_INITIAL, 'Wallet to Deposit (Initial)'),
        (KIND_PROFIT_ACCOUNT, 'Account Profit Accrual'),
        (KIND_PROFIT_DEPOSIT_TO_WALLET, 'Deposit Profit to Wallet'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='transactions')
    source_wallet = models.ForeignKey('Wallet', null=True, blank=True, on_delete=models.SET_NULL, related_name='outgoing_wallet_transactions')
    destination_wallet = models.ForeignKey('Wallet', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_wallet_transactions')
    source_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='outgoing_account_transactions')
    destination_account = models.ForeignKey('Account', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_account_transactions')
    destination_deposit = models.ForeignKey('Deposit', null=True, blank=True, on_delete=models.SET_NULL, related_name='incoming_deposit_transactions')
    amount = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    kind = models.CharField(max_length=40, choices=KIND_CHOICES)
    # Exchange rate to convert non-Rial accounts to wallet IRR and vice versa.
    # If moving account->wallet and account is not rial, wallet_amount = amount * exchange_rate
    # If moving wallet->account non-rial, account_amount = amount / exchange_rate
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    applied = models.BooleanField(default=False)

    def clean(self):
        # Basic validation that at least one source and one destination is set appropriately
        if self.kind in [self.KIND_ADD_TO_WALLET, self.KIND_REMOVE_FROM_WALLET]:
            if not (self.destination_wallet or self.source_wallet):
                from django.core.exceptions import ValidationError
                raise ValidationError('Add/Remove requires wallet.')
            return
        if self.kind == self.KIND_WALLET_TO_DEPOSIT_INITIAL:
            if not (self.source_wallet and self.destination_deposit):
                from django.core.exceptions import ValidationError
                raise ValidationError('Wallet to Deposit requires source_wallet and destination_deposit')
            return
        if not any([self.source_wallet, self.source_account]) or not any([self.destination_wallet, self.destination_account]):
            from django.core.exceptions import ValidationError
            raise ValidationError('Transaction must have a source and a destination.')

    def apply(self):
        # Apply transactional movement with optional conversions
        if self.applied:
            return
        if self.kind == self.KIND_ADD_TO_WALLET:
            if not self.destination_wallet:
                return
            amt = Decimal(self.amount)
            self.destination_wallet.balance += amt
            self.destination_wallet.save(update_fields=['balance', 'updated_at'])
            self.applied = True
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_REMOVE_FROM_WALLET:
            if not self.source_wallet:
                return
            amt = Decimal(self.amount)
            self.source_wallet.balance -= amt
            self.source_wallet.save(update_fields=['balance', 'updated_at'])
            self.applied = True
            self.save(update_fields=['applied'])
            return

        if self.kind == self.KIND_WALLET_TO_DEPOSIT_INITIAL:
            # Move from wallet to create/initialize deposit balance
            amt = Decimal(self.amount)
            self.source_wallet.balance -= amt
            self.source_wallet.save(update_fields=['balance', 'updated_at'])
            if self.destination_deposit:
                self.destination_deposit.amount += amt
                self.destination_deposit.save(update_fields=['amount', 'updated_at'])
            self.applied = True
            self.save(update_fields=['applied'])
            return

        # Currency conversion for account <-> wallet when account is not rial
        def is_account_rial(account: 'Account') -> bool:
            return account.account_type == Account.ACCOUNT_TYPE_RIAL

        # Deduct from sources
        if self.source_wallet:
            amt = Decimal(self.amount)
            self.source_wallet.balance -= amt
            self.source_wallet.save(update_fields=['balance', 'updated_at'])
        if self.source_account:
            amt = Decimal(self.amount)
            self.source_account.balance -= amt
            self.source_account.save(update_fields=['balance', 'updated_at'])

        # Credit destinations, possibly with conversion
        if self.destination_wallet:
            amt = Decimal(self.amount)
            credit_amount = amt
            if self.source_account and not is_account_rial(self.source_account):
                # account -> wallet conversion uses exchange_rate (account unit -> IRR)
                if self.exchange_rate is None:
                    credit_amount = amt
                else:
                    credit_amount = amt * Decimal(self.exchange_rate)
            self.destination_wallet.balance += credit_amount
            self.destination_wallet.save(update_fields=['balance', 'updated_at'])

        if self.destination_account:
            amt = Decimal(self.amount)
            credit_amount = amt
            if not is_account_rial(self.destination_account) and self.source_wallet:
                # wallet(IRR) -> non-rial account, use exchange_rate (account unit -> IRR), so account_amount = wallet_amount / rate
                if self.exchange_rate is None or Decimal(self.exchange_rate) == 0:
                    credit_amount = amt
                else:
                    credit_amount = amt / Decimal(self.exchange_rate)
            self.destination_account.balance += credit_amount
            self.destination_account.save(update_fields=['balance', 'updated_at'])
        self.applied = True
        self.save(update_fields=['applied'])

    def __str__(self):
        return f"Txn({self.kind}) {self.amount} by {self.user.username}"


class AccountDailyBalance(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='daily_balances')
    snapshot_date = models.DateField()
    balance = models.DecimalField(max_digits=18, decimal_places=6)

    class Meta:
        unique_together = ('account', 'snapshot_date')
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"DailyBalance({self.account_id} {self.snapshot_date} {self.balance})"


    def revert(self):
        # Revert the effects of an already applied transaction
        if not self.applied:
            return
        amt = Decimal(self.amount)
        if self.kind == self.KIND_ADD_TO_WALLET and self.destination_wallet:
            self.destination_wallet.balance -= amt
            self.destination_wallet.save(update_fields=['balance', 'updated_at'])
            self.applied = False
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_REMOVE_FROM_WALLET and self.source_wallet:
            self.source_wallet.balance += amt
            self.source_wallet.save(update_fields=['balance', 'updated_at'])
            self.applied = False
            self.save(update_fields=['applied'])
            return
        if self.kind == self.KIND_WALLET_TO_DEPOSIT_INITIAL and self.source_wallet:
            self.source_wallet.balance += amt
            self.source_wallet.save(update_fields=['balance', 'updated_at'])
            if self.destination_deposit:
                self.destination_deposit.amount -= amt
                self.destination_deposit.save(update_fields=['amount', 'updated_at'])
            self.applied = False
            self.save(update_fields=['applied'])
            return

        def is_account_rial(account: 'Account') -> bool:
            return account.account_type == Account.ACCOUNT_TYPE_RIAL

        # Reverse credit to destinations
        if self.destination_wallet:
            credit_amount = amt
            if self.source_account and not is_account_rial(self.source_account):
                if self.exchange_rate is None:
                    credit_amount = amt
                else:
                    credit_amount = amt * Decimal(self.exchange_rate)
            self.destination_wallet.balance -= credit_amount
            self.destination_wallet.save(update_fields=['balance', 'updated_at'])

        if self.destination_account:
            credit_amount = amt
            if not is_account_rial(self.destination_account) and self.source_wallet:
                if self.exchange_rate is None or Decimal(self.exchange_rate) == 0:
                    credit_amount = amt
                else:
                    credit_amount = amt / Decimal(self.exchange_rate)
            self.destination_account.balance -= credit_amount
            self.destination_account.save(update_fields=['balance', 'updated_at'])

        # Reverse deductions from sources
        if self.source_wallet:
            self.source_wallet.balance += amt
            self.source_wallet.save(update_fields=['balance', 'updated_at'])
        if self.source_account:
            self.source_account.balance += amt
            self.source_account.save(update_fields=['balance', 'updated_at'])

        self.applied = False
        self.save(update_fields=['applied'])


# Create your models here.
