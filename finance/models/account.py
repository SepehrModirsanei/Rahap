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
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    initial_balance = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    # Funding options
    FUNDING_SOURCE_WALLET = 'wallet'
    FUNDING_SOURCE_TRANSACTION = 'transaction'
    FUNDING_SOURCE_NONE = 'none'
    FUNDING_SOURCE_CHOICES = [
        (FUNDING_SOURCE_WALLET, 'Fund from User Wallet'),
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
        incoming = Transaction.objects.filter(
            destination_account=self,
            applied=True
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        outgoing = Transaction.objects.filter(
            source_account=self,
            applied=True
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        return self.initial_balance + incoming - outgoing

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            # Auto-select user's wallet if not specified
            if not self.wallet_id and self.user_id:
                # Ensure user has a wallet
                if not hasattr(self.user, 'wallet'):
                    from .wallet import Wallet
                    Wallet.objects.create(user=self.user)
                self.wallet = self.user.wallet
            
            # Handle initial funding
            if self.funding_source == self.FUNDING_SOURCE_WALLET and self.initial_funding_amount > 0:
                # Validate sufficient wallet balance
                if self.wallet.balance < self.initial_funding_amount:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(f'Insufficient wallet balance. Available: {self.wallet.balance}, Required: {self.initial_funding_amount}')
                
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
            source_wallet=None,
            destination_wallet=None,
            amount=profit,
            kind=Transaction.KIND_PROFIT_ACCOUNT,
        )

    def __str__(self):
        return f"Account({self.user.username}:{self.name}:{self.account_type})"
