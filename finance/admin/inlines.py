"""
Admin Inline Classes

This module contains all inline admin classes for the finance application.
Inlines are used to display related objects within other admin pages.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from ..models import Account, Deposit, Transaction, TransactionStateLog
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


class ReadOnlyTransactionInline(admin.TabularInline):
    """Read-only inline for transaction relationships"""
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('transaction_code', 'user', 'kind', 'amount', 'exchange_rate', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'get_persian_created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
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


class TransactionStateLogInline(admin.TabularInline):
    """Inline for transaction state logs"""
    model = TransactionStateLog
    extra = 0
    can_delete = False
    readonly_fields = ('get_transaction_code', 'get_transaction_kind_persian', 'get_transaction_amount', 'get_exchange_rate', 'get_from_state_persian', 'get_to_state_persian', 'changed_by', 'get_persian_created_at', 'get_persian_changed_at', 'notes')
    fields = readonly_fields

    def get_transaction_code(self, obj):
        """Display transaction code"""
        if obj.transaction:
            return obj.transaction.transaction_code
        return '-'
    get_transaction_code.short_description = 'کد تراکنش'

    def get_transaction_kind_persian(self, obj):
        """Display Persian transaction kind"""
        if obj.transaction:
            return obj.transaction.get_kind_display()
        return '-'
    get_transaction_kind_persian.short_description = 'نوع تراکنش'

    def get_transaction_amount(self, obj):
        """Display transaction amount"""
        if obj.transaction:
            return f"{obj.transaction.amount:,.2f}"
        return '-'
    get_transaction_amount.short_description = 'مبلغ'

    def get_exchange_rate(self, obj):
        """Display exchange rate"""
        if obj.transaction:
            if obj.transaction.kind == obj.transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT:
                if obj.transaction.exchange_rate:
                    return f"{obj.transaction.exchange_rate:,.6f}"
                else:
                    return "1.000000"  # Default for same currency
            else:
                return "-"  # Not applicable for other transaction types
        return '-'
    get_exchange_rate.short_description = 'نرخ تبدیل'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AccountInline(admin.TabularInline):
    """Inline admin for user accounts"""
    model = Account
    extra = 0
    readonly_fields = ('balance_display', 'get_persian_created_at', 'get_profit_calculation_info', 'transaction_count')
    fields = ('name', 'account_type', 'initial_balance', 'balance_display', 'monthly_profit_rate', 'transaction_count', 'get_persian_created_at', 'get_profit_calculation_info')
    ordering = ('-created_at',)
    can_delete = False
    
    def balance_display(self, obj):
        if obj.pk:
            return f"{obj.balance:,.2f} ریال"
        return "N/A"
    balance_display.short_description = 'موجودی فعلی'
    
    def transaction_count(self, obj):
        if obj.pk:
            incoming = obj.incoming_account_transactions.count()
            outgoing = obj.outgoing_account_transactions.count()
            return f"ورودی: {incoming} | خروجی: {outgoing}"
        return "N/A"
    transaction_count.short_description = 'تعداد تراکنش‌ها'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


class DepositInline(admin.TabularInline):
    """Inline admin for user deposits"""
    model = Deposit
    extra = 0
    readonly_fields = ('balance_display', 'get_persian_created_at', 'get_profit_calculation_info', 'transaction_count')
    fields = ('initial_balance', 'balance_display', 'monthly_profit_rate', 'transaction_count', 'get_persian_created_at', 'get_profit_calculation_info')
    ordering = ('-created_at',)
    can_delete = False
    
    def balance_display(self, obj):
        if obj.pk:
            return f"{obj.balance:,.2f} ریال"
        return "N/A"
    balance_display.short_description = 'موجودی فعلی'
    
    def transaction_count(self, obj):
        if obj.pk:
            transactions = obj.incoming_deposit_transactions.count()
            return f"تعداد تراکنش‌ها: {transactions}"
        return "N/A"
    transaction_count.short_description = 'تراکنش‌ها'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


class TransactionInline(admin.TabularInline):
    """Inline admin for user transactions"""
    model = Transaction
    extra = 0
    readonly_fields = ('transaction_summary', 'get_persian_created_at', 'amount_display', 'state_display')
    fields = ('kind', 'transaction_summary', 'amount_display', 'state_display', 'applied', 'scheduled_for', 'get_persian_created_at')
    ordering = ('-created_at',)
    can_delete = False
    
    def transaction_summary(self, obj):
        """Create a summary of the transaction with clickable links"""
        if not obj.pk:
            return "N/A"
        
        # Create clickable links to related objects
        links = []
        
        if obj.source_account:
            account_url = reverse('admin:finance_account_change', args=[obj.source_account.pk])
            links.append(f'<a href="{account_url}" target="_blank">از: {obj.source_account.name}</a>')
        
        if obj.destination_account:
            account_url = reverse('admin:finance_account_change', args=[obj.destination_account.pk])
            links.append(f'<a href="{account_url}" target="_blank">به: {obj.destination_account.name}</a>')
        
        if obj.destination_deposit:
            deposit_url = reverse('admin:finance_deposit_change', args=[obj.destination_deposit.pk])
            links.append(f'<a href="{deposit_url}" target="_blank">به سپرده: {obj.destination_deposit.name}</a>')
        
        # Add exchange rate if present
        exchange_info = ""
        if obj.exchange_rate:
            exchange_info = f" (نرخ: {obj.exchange_rate})"
        
        # Combine all information
        summary_parts = [f"<strong>{obj.get_kind_display()}</strong>"]
        if links:
            summary_parts.extend(links)
        if exchange_info:
            summary_parts.append(exchange_info)
        
        return mark_safe(" | ".join(summary_parts))
    
    transaction_summary.short_description = 'جزئیات تراکنش'
    
    def amount_display(self, obj):
        """Display amount with proper formatting"""
        if obj.pk:
            return f"{obj.amount:,.2f} ریال"
        return "N/A"
    amount_display.short_description = 'مبلغ'
    
    def state_display(self, obj):
        """Display state with color coding"""
        if not obj.pk:
            return "N/A"
        
        state_colors = {
            'done': 'green',
            'waiting_treasury': 'orange',
            'waiting_sandogh': 'blue',
            'verified_khazanedar': 'purple',
            'rejected': 'red',
            'waiting_finance_manager': 'brown'
        }
        
        color = state_colors.get(obj.state, 'black')
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{obj.get_state_display()}</span>')
    state_display.short_description = 'وضعیت'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('source_account', 'destination_account', 'destination_deposit')
    
    def has_add_permission(self, request, obj=None):
        # Disable adding transactions from user inline - use dedicated transaction admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Allow viewing but not editing from user inline
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Disable deleting transactions from user inline
        return False


