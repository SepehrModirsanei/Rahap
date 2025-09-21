from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from persiantools.jdatetime import JalaliDateTime


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
        """Return Persian formatted creation date"""
        if self.created_at:
            jalali = JalaliDateTime(self.created_at)
            return jalali.strftime('%Y/%m/%d %H:%M:%S')
        return '-'
    
    def get_persian_changed_at(self):
        """Return Persian formatted change date"""
        if self.changed_at:
            jalali = JalaliDateTime(self.changed_at)
            return jalali.strftime('%Y/%m/%d %H:%M:%S')
        return '-'

    def __str__(self):
        return f"Txn {self.transaction.id}: {self.from_state} → {self.to_state} by {self.changed_by} at {self.changed_at}"
