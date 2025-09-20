from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

from .models import User, Account, Deposit, Transaction


@receiver(post_save, sender=User)
def create_user_default_account(sender, instance: User, created: bool, **kwargs):
    """Ensure every user has at least one default account"""
    if created:
        # Create default rial account if none exists
        if not instance.accounts.exists():
            Account.objects.create(
                user=instance,
                name='Default Rial Account',
                account_type=Account.ACCOUNT_TYPE_RIAL,
                initial_balance=Decimal('0.00')
            )


@receiver(post_save, sender=Deposit)
def fund_deposit_on_create(sender, instance: Deposit, created: bool, **kwargs):
    """Handle deposit funding based on funding source"""
    if created and instance.initial_balance and instance.initial_balance > 0:
        if instance.funding_source == instance.FUNDING_SOURCE_TRANSACTION:
            # Find user's default account to fund from
            default_account = instance.user.accounts.filter(account_type='rial').first()
            if default_account:
                # Create and apply account -> deposit transaction
                txn = Transaction.objects.create(
                    user=instance.user,
                    source_account=default_account,
                    destination_deposit=instance,
                    amount=instance.initial_balance,
                    kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
                    state=Transaction.STATE_DONE
                )
                txn.apply()
        # For FUNDING_SOURCE_NONE, no funding transaction is created


