from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta


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
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    initial_balance = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    # Funding options
    FUNDING_SOURCE_TRANSACTION = 'transaction'
    FUNDING_SOURCE_NONE = 'none'
    FUNDING_SOURCE_CHOICES = [
        (FUNDING_SOURCE_TRANSACTION, 'Fund from Transaction'),
        (FUNDING_SOURCE_NONE, 'No Initial Funding'),
    ]
    funding_source = models.CharField(max_length=20, choices=FUNDING_SOURCE_CHOICES, default=FUNDING_SOURCE_NONE)
    initial_funding_amount = models.DecimalField(max_digits=18, decimal_places=6, default=0, validators=[MinValueValidator(0)])
    # e.g., 2.5 => 2.5% monthly
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def balance(self):
        """Calculate current balance based on initial balance and all transactions"""
        from .transaction import Transaction
        
        # Get all transactions that affect this account
        incoming_txns = Transaction.objects.filter(
            destination_account=self,
            applied=True
        )
        
        outgoing_txns = Transaction.objects.filter(
            source_account=self,
            applied=True
        )
        
        # Calculate incoming amount (considering exchange rates)
        incoming_total = Decimal('0')
        for txn in incoming_txns:
            if txn.kind == Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT:
                # For account-to-account transfers, we need to consider exchange rates
                if (txn.source_account and txn.destination_account and 
                    txn.source_account.account_type != txn.destination_account.account_type and
                    txn.exchange_rate):
                    # Cross-currency transfer: convert amount using exchange rate
                    # The transaction amount is in source currency, we need destination currency
                    converted_amount = Decimal(txn.amount) * Decimal(txn.exchange_rate)
                    incoming_total += converted_amount
                else:
                    # Same currency or no exchange rate needed
                    incoming_total += Decimal(txn.amount)
            elif txn.kind == Transaction.KIND_CREDIT_INCREASE:
                # Credit increase adds money directly to this account
                incoming_total += Decimal(txn.amount)
            elif txn.kind == Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT:
                # Profit from deposit goes to this account
                incoming_total += Decimal(txn.amount)
            else:
                # Other transaction types
                incoming_total += Decimal(txn.amount)
        
        # Calculate outgoing amount (always in this account's currency)
        outgoing_total = sum(Decimal(txn.amount) for txn in outgoing_txns)
        
        return self.initial_balance + incoming_total - outgoing_total

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            # Handle initial funding from transaction
            if self.funding_source == self.FUNDING_SOURCE_TRANSACTION and self.initial_funding_amount > 0:
                # Set initial balance to funding amount
                self.initial_balance = self.initial_funding_amount
        
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
        prev_balance = Decimal(carry.balance) if carry else Decimal(self.initial_balance)
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
        from .transaction import Transaction
        Transaction.objects.create(
            user=self.user,
            source_account=None,
            destination_account=self,
            amount=profit,
            kind=Transaction.KIND_PROFIT_ACCOUNT,
        )

    def __str__(self):
        return f"Account({self.user.username}:{self.name}:{self.account_type})"
