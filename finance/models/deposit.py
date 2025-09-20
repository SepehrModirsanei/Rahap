from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Deposit(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='deposits')
    wallet = models.ForeignKey('Wallet', on_delete=models.CASCADE, related_name='deposits')
    initial_balance = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
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
    funding_source = models.CharField(max_length=20, choices=FUNDING_SOURCE_CHOICES, default=FUNDING_SOURCE_WALLET)
    # Profit goes to wallet (not compounded)
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def amount(self):
        """Alias for initial_balance for backward compatibility"""
        return self.initial_balance

    @property
    def balance(self):
        """Calculate current balance based on initial balance and all transactions"""
        from .transaction import Transaction
        # Get all transactions that affect this deposit
        incoming = Transaction.objects.filter(
            destination_deposit=self,
            applied=True
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        outgoing = Transaction.objects.filter(
            source_deposit=self,
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
        
        super().save(*args, **kwargs)

    def clean(self):
        # Ensure wallet belongs to user
        from django.core.exceptions import ValidationError
        if self.wallet and self.user and self.wallet.user_id != self.user_id:
            raise ValidationError('Wallet must belong to the same user as the deposit.')
        
        # Validate funding based on funding source
        if not self.pk and self.funding_source == self.FUNDING_SOURCE_WALLET and self.initial_balance is not None:
            if Decimal(self.wallet.balance) < Decimal(self.initial_balance):
                raise ValidationError(f'Insufficient wallet balance for initial deposit amount. Available: {self.wallet.balance}, Required: {self.initial_balance}')

    def accrue_monthly_profit(self):
        now = timezone.now()
        if self.monthly_profit_rate and (not self.last_profit_accrual_at or (now - self.last_profit_accrual_at).days >= 28):
            profit = (self.initial_balance * self.monthly_profit_rate) / 100
            # credit wallet
            self.wallet.balance += profit
            self.wallet.save(update_fields=['balance', 'updated_at'])
            self.last_profit_accrual_at = now
            self.save(update_fields=['last_profit_accrual_at', 'updated_at'])
            from .transaction import Transaction
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
        return f"Deposit({self.user.username}) initial_balance={self.initial_balance}"
