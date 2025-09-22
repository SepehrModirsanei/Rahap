from django.db import models
from django.utils.translation import gettext_lazy as _


class DepositDailyBalance(models.Model):
    deposit = models.ForeignKey('Deposit', on_delete=models.CASCADE, related_name='daily_balances')
    snapshot_date = models.DateField()
    balance = models.DecimalField(max_digits=18, decimal_places=6)

    class Meta:
        verbose_name = _('موجودی روزانه سپرده')
        verbose_name_plural = _('موجودی‌های روزانه سپرده')
        unique_together = ('deposit', 'snapshot_date')
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"DepositDailyBalance({self.deposit_id} {self.snapshot_date} {self.balance})"


