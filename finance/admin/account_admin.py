from django.contrib import admin
from django.utils import timezone
from decimal import Decimal
from django.db.models import Avg
from ..models import Account, Transaction, AccountDailyBalance
from .filters import ProfitCalculationFilter
from ..utils import get_persian_date_display
from .inlines import AccountTxnOutInline, AccountTxnInInline
from .mixins import ProfitAccrualMixin, SnapshotMixin


# All inline classes are now imported from inlines.py


@admin.register(Account)
class AccountAdmin(ProfitAccrualMixin, SnapshotMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'get_kind', 'get_unit', 'initial_balance', 'balance_display', 'monthly_profit_rate', 'get_snapshot_count', 'get_persian_created_at', 'get_profit_start_date', 'get_next_profit_date', 'get_average_balance')
    list_filter = ('account_type', ProfitCalculationFilter)
    search_fields = ('user__username', 'name')
    actions = ['accrue_profit_now', 'snapshot_today']
    inlines = [AccountTxnOutInline, AccountTxnInInline]
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('user', 'name', 'account_type', 'monthly_profit_rate')
        }),
        ('موجودی اولیه', {
            'fields': ('initial_balance',),
            'description': 'موجودی اولیه مبلغ شروع برای این حساب است. همه حساب‌ها با موجودی صفر شروع می‌شوند.'
        }),
        ('اطلاعات سود', {
            'fields': ('get_profit_start_date', 'get_next_profit_date', 'get_average_balance'),
            'description': 'اطلاعات مربوط به محاسبه سود ماهانه'
        }),
    )
    readonly_fields = ('get_profit_start_date', 'get_next_profit_date', 'get_average_balance')

    def balance_display(self, obj):
        """Display the current balance of the account"""
        return f"${obj.balance:,.2f}"
    balance_display.short_description = 'موجودی فعلی'
    balance_display.admin_order_field = 'balance'

    def get_profit_start_date(self, obj):
        """Display when profit calculation started for this account"""
        if obj.last_profit_accrual_at:
            return get_persian_date_display(obj.last_profit_accrual_at)
        elif obj.created_at:
            return get_persian_date_display(obj.created_at)
        return "هنوز شروع نشده"
    get_profit_start_date.short_description = 'تاریخ شروع سود'
    get_profit_start_date.admin_order_field = 'last_profit_accrual_at'

    def get_next_profit_date(self, obj):
        """Display when next profit will be calculated"""
        if not obj.monthly_profit_rate or obj.monthly_profit_rate == 0:
            return "سود ماهانه ندارد"
        
        if obj.last_profit_accrual_at:
            # Next profit date is 30 days after last accrual
            next_date = obj.last_profit_accrual_at + timezone.timedelta(days=30)
            return get_persian_date_display(next_date)
        elif obj.created_at:
            # If no profit has been accrued yet, next date is 30 days after account creation
            next_date = obj.created_at + timezone.timedelta(days=30)
            return get_persian_date_display(next_date)
        else:
            # If no creation date available, use current time
            next_date = timezone.now() + timezone.timedelta(days=30)
            return get_persian_date_display(next_date)
    get_next_profit_date.short_description = 'تاریخ سود بعدی'
    get_next_profit_date.admin_order_field = 'last_profit_accrual_at'

    def get_average_balance(self, obj):
        """Display average balance during profit calculation period"""
        if not obj.monthly_profit_rate or obj.monthly_profit_rate == 0:
            return "سود ماهانه ندارد"
        
        # Get daily balance snapshots for this account
        snapshots = AccountDailyBalance.objects.filter(account=obj).order_by('snapshot_date')
        
        if not snapshots.exists():
            return f"${obj.balance:,.2f} (فعلی)"
        
        # Calculate average balance from snapshots
        avg_balance = snapshots.aggregate(avg_balance=Avg('balance'))['avg_balance']
        if avg_balance:
            return f"${avg_balance:,.2f}"
        else:
            return f"${obj.balance:,.2f} (فعلی)"
    get_average_balance.short_description = 'میانگین موجودی'
    get_average_balance.admin_order_field = 'balance'
