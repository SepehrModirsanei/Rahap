from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Deposit(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='deposits')
    initial_balance = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    # Funding options
    FUNDING_SOURCE_TRANSACTION = 'transaction'
    FUNDING_SOURCE_NONE = 'none'
    FUNDING_SOURCE_CHOICES = [
        (FUNDING_SOURCE_TRANSACTION, 'Fund from Transaction'),
        (FUNDING_SOURCE_NONE, 'No Initial Funding'),
    ]
    funding_source = models.CharField(max_length=20, choices=FUNDING_SOURCE_CHOICES, default=FUNDING_SOURCE_NONE)
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
        
        # Deposits can only receive money, not send it
        return self.initial_balance + incoming

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            # Handle initial funding from transaction
            if self.funding_source == self.FUNDING_SOURCE_TRANSACTION and self.initial_balance > 0:
                # Set initial balance to funding amount
                self.initial_balance = self.initial_balance
        
        super().save(*args, **kwargs)

    def clean(self):
        # Validate funding based on funding source
        if not self.pk and self.funding_source == self.FUNDING_SOURCE_TRANSACTION and self.initial_balance is not None:
            # For transaction funding, we'll validate when the transaction is created
            pass

    def accrue_monthly_profit(self):
        now = timezone.now()
        if self.monthly_profit_rate and (not self.last_profit_accrual_at or (now - self.last_profit_accrual_at).days >= 28):
            profit = (self.initial_balance * self.monthly_profit_rate) / 100
            # Find user's default account to credit profit
            default_account = self.user.accounts.filter(account_type='rial').first()
            if not default_account:
                # Create a default rial account if none exists
                from .account import Account
                default_account = Account.objects.create(
                    user=self.user,
                    name='Default Rial Account',
                    account_type=Account.ACCOUNT_TYPE_RIAL,
                    initial_balance=Decimal('0.00')
                )
            
            self.last_profit_accrual_at = now
            self.save(update_fields=['last_profit_accrual_at', 'updated_at'])
            from .transaction import Transaction
            Transaction.objects.create(
                user=self.user,
                source_account=None,
                destination_account=default_account,
                amount=profit,
                kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            )

    def __str__(self):
        return f"Deposit({self.user.username}) initial_balance={self.initial_balance}"
