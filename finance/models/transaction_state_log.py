from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class TransactionStateLog(models.Model):
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, related_name='state_logs')
    from_state = models.CharField(max_length=40, null=True, blank=True)
    to_state = models.CharField(max_length=40)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Transaction State Log'
        verbose_name_plural = 'Transaction State Logs'

    def __str__(self):
        return f"Txn {self.transaction.id}: {self.from_state} → {self.to_state} by {self.changed_by} at {self.changed_at}"
