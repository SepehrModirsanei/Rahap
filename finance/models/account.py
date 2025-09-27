from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, timedelta
from ..utils import get_persian_date_display


class Account(models.Model):
    ACCOUNT_TYPE_RIAL = 'rial'
    ACCOUNT_TYPE_GOLD = 'gold'
    ACCOUNT_TYPE_USD = 'usd'
    ACCOUNT_TYPE_EUR = 'eur'
    ACCOUNT_TYPE_GBP = 'gbp'
    ACCOUNT_TYPE_CHOICES = [
        (ACCOUNT_TYPE_RIAL, _('حساب ریالی')),
        (ACCOUNT_TYPE_GOLD, _('حساب طلا')),
        (ACCOUNT_TYPE_USD, _('حساب دلاری (USD)')),
        (ACCOUNT_TYPE_EUR, _('حساب یورویی (EUR)')),
        (ACCOUNT_TYPE_GBP, _('حساب پوندی (GBP)')),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='accounts', verbose_name=_('کاربر'))
    name = models.CharField(max_length=100, verbose_name=_('نام حساب'))
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, verbose_name=_('نوع حساب'))
    initial_balance = models.DecimalField(max_digits=18, decimal_places=6, default=0, verbose_name=_('موجودی اولیه'))
    monthly_profit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name=_('نرخ سود ماهانه'))
    # e.g., 2.5 => 2.5% monthly
    last_profit_accrual_at = models.DateTimeField(null=True, blank=True, verbose_name=_('آخرین تعلق سود'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ بروزرسانی'))
    
    class Meta:
        verbose_name = _('حساب')
        verbose_name_plural = _('حساب‌ها')

    def get_unit(self):
        """Return unit label for this account's amounts."""
        if self.account_type == self.ACCOUNT_TYPE_RIAL:
            return 'ریال'
        if self.account_type == self.ACCOUNT_TYPE_GOLD:
            return 'گرم'
        if self.account_type == self.ACCOUNT_TYPE_USD:
            return 'دلار'
        if self.account_type == self.ACCOUNT_TYPE_EUR:
            return 'یورو'
        if self.account_type == self.ACCOUNT_TYPE_GBP:
            return 'پوند'
        return ''
    get_unit.short_description = 'واحد'

    def get_kind(self):
        """Return human-readable kind for this account (context-based)."""
        return self.get_account_type_display()
    get_kind.short_description = 'نوع'

    def get_snapshot_count(self):
        try:
            return self.daily_balances.count()
        except Exception:
            return 0
    get_snapshot_count.short_description = 'تعداد اسنپ‌شات'

    @property
    def balance(self):
        """Calculate current balance based on initial balance and all transactions"""
        from django.db.models import Sum, Case, When, F, Q
        
        # Optimized: Use database aggregation instead of Python loops
        # Use apps.get_model to avoid circular imports
        from django.apps import apps
        Transaction = apps.get_model('finance', 'Transaction')
        
        # Calculate incoming amount using database aggregation
        incoming_result = Transaction.objects.filter(
            destination_account=self,
            applied=True
        ).aggregate(
            total=Sum(
                Case(
                    # For account-to-account transfers, use destination_amount if available
                    When(
                        kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                        destination_account=self,
                        destination_amount__isnull=False,
                        then=F('destination_amount')
                    ),
                    # Otherwise use regular amount
                    default=F('amount')
                )
            )
        )
        
        # Calculate outgoing amount using database aggregation
        outgoing_result = Transaction.objects.filter(
            source_account=self,
            applied=True
        ).aggregate(
            total=Sum('amount')
        )
        
        incoming_total = incoming_result['total'] or Decimal('0')
        outgoing_total = outgoing_result['total'] or Decimal('0')
        
        return self.initial_balance + incoming_total - outgoing_total

    def save(self, *args, **kwargs):
        # All accounts start with zero balance - no funding logic needed
        super().save(*args, **kwargs)

    def accrue_monthly_profit(self):
        now = timezone.now()
        if not self.monthly_profit_rate:
            return
        # Check if enough time has passed since last profit accrual (30 days)
        if self.last_profit_accrual_at and (now - self.last_profit_accrual_at).days < 30:
            return
        # Compute profit based on daily snapshots over last 30 days ending yesterday
        period_end = date.today()
        period_start = period_end - timedelta(days=30)
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
                segments.append((prev_date, d, Decimal(snap.balance)))
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
        # Monthly profit = rate% * (sum of daily balances / 30)
        average_balance = weighted_sum / Decimal(30)
        profit = (average_balance * Decimal(self.monthly_profit_rate)) / Decimal(100)
        if profit <= 0:
            return
        
        # Create profit transaction instead of directly modifying balance
        # Use apps.get_model to avoid circular imports
        from django.apps import apps
        Transaction = apps.get_model('finance', 'Transaction')
        profit_transaction = Transaction.objects.create(
            user=self.user,
            source_account=None,
            destination_account=self,
            amount=profit,
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        profit_transaction.apply()
        
        # Update the last profit accrual timestamp
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
        """Return profit calculation start date and average balance"""
        if self.last_profit_accrual_at:
            # Calculate average balance for the 30-day period
            from django.utils import timezone
            from datetime import timedelta
            from .account_daily_balance import AccountDailyBalance
            
            # Get the start of the profit calculation period (30 days before last accrual)
            profit_start_date = self.last_profit_accrual_at - timedelta(days=30)
            
            # Calculate average balance over the 30-day period
            daily_balances = AccountDailyBalance.objects.filter(
                account=self,
                snapshot_date__gte=profit_start_date.date(),
                snapshot_date__lte=self.last_profit_accrual_at.date()
            ).order_by('snapshot_date')
            
            if daily_balances.exists():
                total_balance = sum(balance.balance for balance in daily_balances)
                avg_balance = total_balance / daily_balances.count()
                return f"شروع: {get_persian_date_display(profit_start_date)} - میانگین: ${avg_balance:,.2f}"
            else:
                return f"شروع: {get_persian_date_display(profit_start_date)} - میانگین: ${self.initial_balance:,.2f}"
        else:
            return "شروع نشده"
    get_profit_calculation_info.short_description = 'اطلاعات سود'

    def __str__(self):
        return f"Account({self.user.username}:{self.name}:{self.account_type})"
