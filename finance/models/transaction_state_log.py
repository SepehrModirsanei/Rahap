from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..utils import get_persian_date_display


class TransactionStateLog(models.Model):
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, related_name='state_logs')
    from_state = models.CharField(max_length=40, null=True, blank=True)
    to_state = models.CharField(max_length=40)
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    changed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'گزارش وضعیت تراکنش'
        verbose_name_plural = 'گزارش‌های وضعیت تراکنش'

    def get_persian_created_at(self):
        """Return Persian formatted creation date (localized to Asia/Tehran)"""
        return get_persian_date_display(self.created_at)
    
    def get_persian_changed_at(self):
        """Return Persian formatted change date (localized to Asia/Tehran)"""
        return get_persian_date_display(self.changed_at)

    def get_from_state_persian(self):
        """Return Persian display for from_state using Transaction.STATE_CHOICES"""
        try:
            from .transaction import Transaction
            mapping = dict(Transaction.STATE_CHOICES)
            return mapping.get(self.from_state, self.from_state or '-')
        except Exception:
            return self.from_state or '-'
    get_from_state_persian.short_description = 'از وضعیت'

    def get_to_state_persian(self):
        """Return Persian display for to_state using Transaction.STATE_CHOICES"""
        try:
            from .transaction import Transaction
            mapping = dict(Transaction.STATE_CHOICES)
            return mapping.get(self.to_state, self.to_state or '-')
        except Exception:
            return self.to_state or '-'
    get_to_state_persian.short_description = 'به وضعیت'

    def __str__(self):
        return f"Txn {self.transaction.id}: {self.from_state} → {self.to_state} by {self.changed_by} at {self.changed_at}"
