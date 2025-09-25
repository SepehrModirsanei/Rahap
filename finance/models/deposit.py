from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from ..utils import get_persian_date_display


class Deposit(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='deposits', verbose_name=_('کاربر'))
    initial_balance = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)], verbose_name=_('موجودی اولیه'))
    # Profit rate interpretation depends on profit_kind (monthly/yearly)
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name=_('نرخ سود'))
    # Profit kind: monthly, six-months (semiannual), or yearly (calculation remains daily, payout window differs)
    PROFIT_KIND_MONTHLY = 'monthly'
    PROFIT_KIND_SEMIANNUAL = 'semiannual'
    PROFIT_KIND_YEARLY = 'yearly'
    PROFIT_KIND_CHOICES = [
        (PROFIT_KIND_MONTHLY, _('ماهانه')),
        (PROFIT_KIND_SEMIANNUAL, _('شش‌ماهه')),
        (PROFIT_KIND_YEARLY, _('سالانه')),
    ]
    profit_kind = models.CharField(max_length=10, choices=PROFIT_KIND_CHOICES, default=PROFIT_KIND_MONTHLY, verbose_name=_('نوع سود'))
    # Breakage coefficient (نرخ ضریب شکست) as percentage 0-100
    breakage_coefficient = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name=_('نرخ ضریب شکست (%)'))
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
        if not self.monthly_profit_rate:
            return
        # Determine accrual window based on profit kind (still calculated daily)
        if self.profit_kind == self.PROFIT_KIND_MONTHLY:
            window_days = 30
        elif self.profit_kind == self.PROFIT_KIND_SEMIANNUAL:
            window_days = 180
        else:
            window_days = 365
        # Check if enough time has passed since last profit accrual
        if self.last_profit_accrual_at and (now - self.last_profit_accrual_at).days < window_days:
            return
        
        # Compute profit based on daily snapshots over last window_days ending yesterday
        from datetime import date, timedelta
        period_end = date.today()
        period_start = period_end - timedelta(days=window_days)
        snapshots = list(self.daily_balances.filter(snapshot_date__gt=period_start).order_by('snapshot_date'))
        # Get carry snapshot on or before start
        carry = self.daily_balances.filter(snapshot_date__lte=period_start).order_by('-snapshot_date').first()
        segments = []
        # Build segments between dates with constant balance
        prev_date = period_start
        prev_balance = Decimal(carry.balance) if carry else Decimal(self.initial_balance)
        for snap in snapshots:
            d = snap.snapshot_date
            if d > prev_date:
                segments.append((prev_date, d, prev_balance))
            prev_date = d
            prev_balance = Decimal(snap.balance)
        # Last segment until period_end
        if prev_date < period_end:
            segments.append((prev_date, period_end, prev_balance))
        # Sum daily balances
        total_days = Decimal(0)
        weighted_sum = Decimal(0)
        for start, end, bal in segments:
            days = Decimal((end - start).days)
            if days > 0:
                total_days += days
                weighted_sum += (bal * days)
        if total_days == 0:
            return
        # Profit = rate% * (sum of daily balances / window_days)
        average_balance = weighted_sum / Decimal(window_days)
        profit = (average_balance * Decimal(self.monthly_profit_rate)) / Decimal(100)
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
            if self.profit_kind == self.PROFIT_KIND_MONTHLY:
                days = 30
            elif self.profit_kind == self.PROFIT_KIND_SEMIANNUAL:
                days = 180
            else:
                days = 365
            if self.last_profit_accrual_at:
                next_profit_date = self.last_profit_accrual_at + timezone.timedelta(days=days)
            elif self.created_at:
                next_profit_date = self.created_at + timezone.timedelta(days=days)
        except Exception:
            next_profit_date = None
        
        start_str = get_persian_date_display(profit_start_date) if profit_start_date else '-'
        next_str = get_persian_date_display(next_profit_date) if next_profit_date else '-'
        avg_balance = self.initial_balance if self.initial_balance is not None else Decimal('0.00')
        return f"شروع: {start_str} - میانگین: ${avg_balance:,.2f} - سود بعدی: {next_str}"
    get_profit_calculation_info.short_description = 'اطلاعات سود'

    def __str__(self):
        return f"Deposit({self.user.username}) initial_balance={self.initial_balance}"
