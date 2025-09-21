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
                # Also store the old created_at for consistency
                instance._old_created_at = old_instance.created_at
        except Transaction.DoesNotExist:
            pass


@receiver(post_save, sender=Transaction)
def create_state_log_entry(sender, instance, created, **kwargs):
    """Create state log entry after saving the transaction"""
    from django.utils import timezone
    
    if created:
        # New transaction - log initial state
        now = timezone.now()
        TransactionStateLog.objects.create(
            transaction=instance,
            from_state=None,
            to_state=instance.state,
            changed_by=getattr(instance, '_changed_by', None),
            created_at=now,
            changed_at=now,
            notes="Initial state"
        )
    elif getattr(instance, '_state_changed', False):
        # State changed - log the change
        now = timezone.now()
        
        # Get the previous log entry to maintain created_at consistency
        previous_log = TransactionStateLog.objects.filter(
            transaction=instance
        ).order_by('-changed_at').first()
        
        # Use the original transaction created_at for consistency
        original_created_at = getattr(instance, '_old_created_at', instance.created_at)
        
        TransactionStateLog.objects.create(
            transaction=instance,
            from_state=getattr(instance, '_old_state', None),
            to_state=instance.state,
            changed_by=getattr(instance, '_changed_by', None),
            created_at=original_created_at,  # Keep original creation time
            changed_at=now,  # Current change time
            notes=f"State changed from {getattr(instance, '_old_state', 'None')} to {instance.state}"
        )
