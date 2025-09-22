from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from ..utils import get_persian_date_display


class Deposit(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='deposits', verbose_name=_('کاربر'))
    initial_balance = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)], verbose_name=_('موجودی اولیه'))
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name=_('نرخ سود ماهانه'))
    # Profit goes to base account (not compounded)
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True, verbose_name=_('آخرین تعلق سود'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    class Meta:
        verbose_name = _('سپرده')
        verbose_name_plural = _('سپرده‌ها')

    @property
    def amount(self):
        """Alias for initial_balance for backward compatibility"""
        return self.initial_balance

    @property
    def balance(self):
        """Calculate current balance based on initial balance and all transactions"""
        from .transaction import Transaction
        # Get all transactions that affect this deposit
        incoming = Transaction.objects.filter(
            destination_deposit=self,
            applied=True
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        # Deposits can only receive money, not send it
        return self.initial_balance + incoming

    def save(self, *args, **kwargs):
        # All deposits start with zero balance - no funding logic needed
        super().save(*args, **kwargs)

    def clean(self):
        # No funding validation needed - all deposits start with zero balance
        pass

    def accrue_monthly_profit(self):
        now = timezone.now()
        if self.monthly_profit_rate and (not self.last_profit_accrual_at or (now - self.last_profit_accrual_at).days >= 30):
            # Calculate profit based on current deposit amount (not just initial balance)
            profit = (self.initial_balance * self.monthly_profit_rate) / 100
            if profit <= 0:
                return
                
            # Find user's base account (حساب پایه) to credit profit.
            # Fallbacks: any rial account; otherwise create one.
            base_account = self.user.accounts.filter(account_type='rial', name='حساب پایه').first()
            if not base_account:
                base_account = self.user.accounts.filter(account_type='rial').first()
            if not base_account:
                from .account import Account
                base_account = Account.objects.create(
                    user=self.user,
                    name='حساب پایه',
                    account_type=Account.ACCOUNT_TYPE_RIAL,
                    initial_balance=Decimal('0.00')
                )
            
            # Create and apply profit transaction
            from .transaction import Transaction
            profit_transaction = Transaction.objects.create(
                user=self.user,
                source_account=None,
                destination_account=base_account,
                amount=profit,
                kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
                state=Transaction.STATE_DONE
            )
            profit_transaction.apply()
            
            # Update only the timestamp (profit goes to user's base account, not back to deposit)
            self.last_profit_accrual_at = now
            self.save(update_fields=['last_profit_accrual_at', 'updated_at'])

    def get_persian_created_at(self):
        """Return Persian date for created_at"""
        return get_persian_date_display(self.created_at)
    get_persian_created_at.short_description = 'تاریخ ایجاد'
    
    def get_persian_updated_at(self):
        """Return Persian date for updated_at"""
        return get_persian_date_display(self.updated_at)
    get_persian_updated_at.short_description = 'تاریخ بروزرسانی'
    
    def get_persian_last_profit_accrual(self):
        """Return Persian date for last_profit_accrual_at"""
        return get_persian_date_display(self.last_profit_accrual_at)
    get_persian_last_profit_accrual.short_description = 'آخرین سود'
    
    def get_profit_calculation_info(self):
        """Return profit calculation start date, average balance, and next profit date"""
        # For deposits, the profit calculation tracking starts at creation time
        # (even before the first accrual happens). Average is the current
        # initial_balance (which may include accumulated profits over time).
        profit_start_date = self.created_at
        
        # Calculate next profit date
        next_profit_date = None
        try:
            if self.last_profit_accrual_at:
                next_profit_date = self.last_profit_accrual_at + timezone.timedelta(days=30)
            elif self.created_at:
                next_profit_date = self.created_at + timezone.timedelta(days=30)
        except Exception:
            next_profit_date = None
        
        start_str = get_persian_date_display(profit_start_date) if profit_start_date else '-'
        next_str = get_persian_date_display(next_profit_date) if next_profit_date else '-'
        return f"شروع: {start_str} - میانگین: ${self.initial_balance:,.2f} - سود بعدی: {next_str}"
    get_profit_calculation_info.short_description = 'اطلاعات سود'

    def __str__(self):
        return f"Deposit({self.user.username}) initial_balance={self.initial_balance}"
