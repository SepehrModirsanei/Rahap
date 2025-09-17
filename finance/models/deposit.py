from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


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
        return f"Deposit({self.user.username}) amount={self.amount}"
