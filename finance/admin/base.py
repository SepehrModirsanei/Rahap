"""
Base Admin Classes for Finance Application

This module contains base admin classes that can be extended
by different admin sites to reduce code duplication.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
from ..models import User, Account, Deposit, Transaction, AccountDailyBalance
from ..forms import TransactionAdminForm
from .transaction_state_log_admin import TransactionStateLogInline
from ..utils import get_persian_date_display


class BaseTransactionInline(admin.TabularInline):
    """Base inline for transaction relationships"""
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'kind', 'amount', 'exchange_rate', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


class AccountTxnOutInline(BaseTransactionInline):
    """Inline for outgoing transactions from accounts"""
    fk_name = 'source_account'
    verbose_name = 'Outgoing Transactions'
    verbose_name_plural = 'Outgoing Transactions'


class AccountTxnInInline(BaseTransactionInline):
    """Inline for incoming transactions to accounts"""
    fk_name = 'destination_account'
    verbose_name = 'Incoming Transactions'
    verbose_name_plural = 'Incoming Transactions'


class DepositTxnInInline(BaseTransactionInline):
    """Inline for transactions to deposits"""
    fk_name = 'destination_deposit'
    verbose_name = 'Deposit Transactions'
    verbose_name_plural = 'Deposit Transactions'


class BaseUserAdmin(admin.ModelAdmin):
    """Base admin class for User model"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined_display')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login', 'user_id_display')
    fieldsets = (
        ('Personal Information', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'user_id_display')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )

    def date_joined_display(self, obj):
        """Display Persian date for date_joined"""
        return get_persian_date_display(obj.date_joined)
    date_joined_display.short_description = 'تاریخ عضویت'

    def user_id_display(self, obj):
        """Display user ID"""
        return obj.short_id
    user_id_display.short_description = 'شناسه کاربر'


class BaseAccountAdmin(admin.ModelAdmin):
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

    def balance_display(self, obj):
        """Display account balance with formatting"""
        return f"{obj.balance:,.2f}"
    balance_display.short_description = 'موجودی'

    def created_at_display(self, obj):
        """Display Persian date for created_at"""
        return get_persian_date_display(obj.created_at)
    created_at_display.short_description = 'تاریخ ایجاد'


class BaseDepositAdmin(admin.ModelAdmin):
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

    def balance_display(self, obj):
        """Display deposit balance with formatting"""
        return f"{obj.balance:,.2f}"
    balance_display.short_description = 'موجودی'

    def created_at_display(self, obj):
        """Display Persian date for created_at"""
        return get_persian_date_display(obj.created_at)
    created_at_display.short_description = 'تاریخ ایجاد'


class BaseTransactionAdmin(admin.ModelAdmin):
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

    def created_at_display(self, obj):
        """Display Persian date for created_at"""
        return get_persian_date_display(obj.created_at)
    created_at_display.short_description = 'تاریخ ایجاد'


class BaseAccountDailyBalanceAdmin(admin.ModelAdmin):
    """Base admin class for AccountDailyBalance model"""
    list_display = ('account', 'get_owner', 'get_persian_snapshot_date', 'balance_display', 'get_snapshot_total')
    list_filter = ('snapshot_date',)
    search_fields = ('account__name', 'account__user__username')
    readonly_fields = ('balance_display',)
    fieldsets = (
        ('Balance Information', {
            'fields': ('account', 'snapshot_date', 'balance_display')
        }),
    )

    def balance_display(self, obj):
        """Display balance with formatting"""
        return f"{obj.balance:,.2f}"
    balance_display.short_description = 'موجودی'

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


# Mixin classes for different permission levels
class ReadOnlyMixin:
    """Mixin for read-only admin classes"""
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class TreasuryMixin:
    """Mixin for treasury admin classes with full permissions"""
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class OperationMixin:
    """Mixin for operation admin classes with limited permissions"""
    
    def has_add_permission(self, request):
        return request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        return False  # Operations staff cannot delete


class AnalyticsMixin:
    """Mixin for analytics admin classes with enhanced display"""
    
    def get_queryset(self, request):
        """Override to add analytics-specific filtering"""
        return super().get_queryset(request)
    
    def changelist_view(self, request, extra_context=None):
        """Add analytics context to changelist"""
        extra_context = extra_context or {}
        extra_context['analytics_mode'] = True
        return super().changelist_view(request, extra_context)
