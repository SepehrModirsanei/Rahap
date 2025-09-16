from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, Wallet, Deposit, Transaction


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance: User, created: bool, **kwargs):
    if created:
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=Deposit)
def fund_deposit_on_create(sender, instance: Deposit, created: bool, **kwargs):
    if created and instance.amount and instance.amount > 0:
        # Create and apply wallet -> deposit transaction
        txn = Transaction.objects.create(
            user=instance.user,
            source_wallet=instance.wallet,
            destination_deposit=instance,
            amount=instance.amount,
            kind=Transaction.KIND_WALLET_TO_DEPOSIT_INITIAL,
        )
        txn.apply()


