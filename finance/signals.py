from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

from .models import User, Account, Deposit, Transaction


@receiver(post_save, sender=User)
def create_user_default_account(sender, instance: User, created: bool, **kwargs):
    """Ensure every user has at least one default account"""
    if created:
        # Always create default rial account for new users
        Account.objects.create(
            user=instance,
            name='حساب پایه',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('0.00'),
            monthly_profit_rate=Decimal('0.00')
        )


# Deposit funding signal removed - all deposits start with zero balance


