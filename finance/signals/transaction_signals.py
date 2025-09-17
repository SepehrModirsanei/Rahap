from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from ..models import Transaction, TransactionStateLog


@receiver(pre_save, sender=Transaction)
def log_transaction_state_change(sender, instance, **kwargs):
    """Log state changes before saving the transaction"""
    if instance.pk:
        try:
            old_instance = Transaction.objects.get(pk=instance.pk)
            if old_instance.state != instance.state:
                # State changed, we'll log it in post_save
                instance._state_changed = True
                instance._old_state = old_instance.state
        except Transaction.DoesNotExist:
            pass


@receiver(post_save, sender=Transaction)
def create_state_log_entry(sender, instance, created, **kwargs):
    """Create state log entry after saving the transaction"""
    if created:
        # New transaction - log initial state
        TransactionStateLog.objects.create(
            transaction=instance,
            from_state=None,
            to_state=instance.state,
            changed_by=getattr(instance, '_changed_by', None),
            notes="Initial state"
        )
    elif getattr(instance, '_state_changed', False):
        # State changed - log the change
        TransactionStateLog.objects.create(
            transaction=instance,
            from_state=getattr(instance, '_old_state', None),
            to_state=instance.state,
            changed_by=getattr(instance, '_changed_by', None),
            notes="State changed"
        )
