from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, Wallet, Deposit, Transaction


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance: User, created: bool, **kwargs):
    """Ensure every user has a wallet"""
    if created:
        # Create wallet if it doesn't exist
        wallet, created = Wallet.objects.get_or_create(
            user=instance,
            defaults={'initial_balance': 0, 'currency': 'IRR'}
        )


@receiver(post_save, sender=Deposit)
def fund_deposit_on_create(sender, instance: Deposit, created: bool, **kwargs):
    """Handle deposit funding based on funding source"""
    if created and instance.initial_balance and instance.initial_balance > 0:
        if instance.funding_source == instance.FUNDING_SOURCE_WALLET:
            # Create and apply wallet -> deposit transaction
            txn = Transaction.objects.create(
                user=instance.user,
                source_wallet=instance.wallet,
                destination_deposit=instance,
                amount=instance.initial_balance,
                kind=Transaction.KIND_WALLET_TO_DEPOSIT_INITIAL,
                state=Transaction.STATE_DONE
            )
            txn.apply()
        # For FUNDING_SOURCE_TRANSACTION, the transaction should be created manually
        # For FUNDING_SOURCE_NONE, no funding transaction is created


