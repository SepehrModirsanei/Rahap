"""
Base Admin Classes for Finance Application

This module contains base admin classes that can be extended
by different admin sites to reduce code duplication.
"""

from django.contrib import admin
from decimal import Decimal
from ..models import User, Account, Deposit, Transaction, AccountDailyBalance, DepositDailyBalance
from ..forms import TransactionAdminForm
from .inlines import AccountTxnOutInline, AccountTxnInInline, DepositTxnInInline, TransactionStateLogInline
from .mixins import CommonDisplayMixin
from ..utils import get_persian_date_display


class BaseAccountAdmin(CommonDisplayMixin, admin.ModelAdmin):
    """Base admin class for Account model"""
    list_display = ('user', 'name', 'account_type', 'balance_display', 'monthly_profit_rate', 'created_at_display')
    list_filter = ('account_type', 'created_at')
    search_fields = ('user__username', 'name')
    readonly_fields = ('created_at', 'updated_at', 'balance_display')
    inlines = [AccountTxnInInline, AccountTxnOutInline]
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'name', 'account_type')
        }),
        ('Financial Details', {
            'fields': ('initial_balance', 'monthly_profit_rate', 'balance_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )



class BaseDepositAdmin(CommonDisplayMixin, admin.ModelAdmin):
    """Base admin class for Deposit model"""
    list_display = ('user', 'initial_balance', 'monthly_profit_rate', 'balance_display', 'created_at_display')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at', 'balance_display')
    inlines = [DepositTxnInInline]
    fieldsets = (
        ('Deposit Information', {
            'fields': ('user', 'initial_balance', 'monthly_profit_rate')
        }),
        ('Current Status', {
            'fields': ('balance_display', 'last_profit_accrual_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )



class BaseTransactionAdmin(CommonDisplayMixin, admin.ModelAdmin):
    """Base admin class for Transaction model"""
    form = TransactionAdminForm
    list_display = ('transaction_code', 'user', 'kind', 'amount', 'state', 'applied', 'created_at_display')
    list_filter = ('kind', 'state', 'applied', 'created_at')
    search_fields = ('transaction_code', 'user__username')
    readonly_fields = ('transaction_code', 'created_at', 'applied')
    inlines = [TransactionStateLogInline]
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_code', 'user', 'kind', 'amount', 'state')
        }),
        ('Account Details', {
            'fields': ('source_account', 'destination_account', 'destination_deposit')
        }),
        ('Exchange & Timing', {
            'fields': ('exchange_rate', 'issued_at', 'scheduled_for'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('applied', 'created_at'),
            'classes': ('collapse',)
        }),
    )



class BaseAccountDailyBalanceAdmin(CommonDisplayMixin, admin.ModelAdmin):
    """Base admin class for AccountDailyBalance model"""
    list_display = ('get_account_name', 'get_account_type', 'get_owner', 'get_persian_snapshot_date', 'balance_display', 'get_snapshot_total')
    list_filter = ('snapshot_date',)
    search_fields = ('account__name', 'account__user__username')
    readonly_fields = ('balance_display',)
    fieldsets = (
        ('Balance Information', {
            'fields': ('account', 'snapshot_date', 'balance_display')
        }),
    )


    def get_owner(self, obj):
        try:
            return obj.account.user
        except Exception:
            return '-'
    get_owner.short_description = 'مالک'

    def get_snapshot_total(self, obj):
        try:
            return obj.account.daily_balances.count()
        except Exception:
            return 0
    get_snapshot_total.short_description = 'تعداد اسنپ‌شات‌های حساب'

    def get_account_type(self, obj):
        try:
            return obj.account.get_account_type_display()
        except Exception:
            return '-'
    get_account_type.short_description = 'نوع حساب'

    def get_account_name(self, obj):
        try:
            return obj.account.name
        except Exception:
            return '-'
    get_account_name.short_description = 'نام حساب'


class BaseDepositDailyBalanceAdmin(CommonDisplayMixin, admin.ModelAdmin):
    """Base admin class for DepositDailyBalance model"""
    list_display = ('deposit', 'get_persian_snapshot_date', 'balance_display', 'snapshot_number')
    list_filter = ('snapshot_date',)
    search_fields = ('deposit__user__username',)
    readonly_fields = ('deposit', 'snapshot_date', 'balance', 'snapshot_number', 'get_persian_snapshot_date')
    ordering = ['-snapshot_date']
    
    def get_persian_snapshot_date(self, obj):
        """Display Persian snapshot date"""
        return obj.get_persian_snapshot_date()
    get_persian_snapshot_date.short_description = 'تاریخ'
    get_persian_snapshot_date.admin_order_field = 'snapshot_date'
    
    fieldsets = (
        ('اطلاعات سپرده', {
            'fields': ('deposit',)
        }),
        ('اطلاعات موجودی', {
            'fields': ('snapshot_date', 'get_persian_snapshot_date', 'balance', 'snapshot_number')
        }),
    )


# Import mixins from the dedicated mixins module
from .mixins import ReadOnlyMixin, TreasuryMixin, OperationMixin, AnalyticsMixin
