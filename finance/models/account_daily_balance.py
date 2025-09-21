from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountDailyBalance(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='daily_balances')
    snapshot_date = models.DateField()
    balance = models.DecimalField(max_digits=18, decimal_places=6)

    class Meta:
        verbose_name = _('موجودی روزانه حساب')
        verbose_name_plural = _('موجودی‌های روزانه حساب')
        unique_together = ('account', 'snapshot_date')
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"DailyBalance({self.account_id} {self.snapshot_date} {self.balance})"
