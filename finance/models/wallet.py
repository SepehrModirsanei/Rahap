from django.db import models
from decimal import Decimal


class Wallet(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='wallet')
    initial_balance = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    currency = models.CharField(max_length=10, default='IRR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def balance(self):
        """Calculate current balance based on initial balance and all transactions"""
        from .transaction import Transaction
        # Get all transactions that affect this wallet
        incoming = Transaction.objects.filter(
            destination_wallet=self,
            applied=True
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        outgoing = Transaction.objects.filter(
            source_wallet=self,
            applied=True
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        return self.initial_balance + incoming - outgoing

    def __str__(self):
        return f"Wallet({self.user.username}) {self.balance} {self.currency}"
