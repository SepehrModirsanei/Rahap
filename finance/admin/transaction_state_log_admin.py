from django.contrib import admin
from ..models import TransactionStateLog
from .inlines import TransactionStateLogInline
from .filters import FromStatePersianFilter, ToStatePersianFilter


# All filter classes are now imported from filters.py


@admin.register(TransactionStateLog)
class TransactionStateLogAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'get_transaction_code', 'get_transaction_kind_persian', 'get_transaction_amount', 'get_exchange_rate', 'get_from_state_persian', 'get_to_state_persian', 'changed_by', 'get_persian_created_at', 'get_persian_changed_at')
    list_filter = (FromStatePersianFilter, ToStatePersianFilter, 'changed_at', 'changed_by', 'transaction__kind')
    search_fields = ('transaction__id', 'transaction__transaction_code', 'transaction__user__username', 'changed_by__username')
    readonly_fields = ('transaction', 'get_transaction_code', 'get_transaction_kind_persian', 'get_transaction_amount', 'get_exchange_rate', 'get_from_state_persian', 'get_to_state_persian', 'changed_by', 'get_persian_created_at', 'get_persian_changed_at', 'notes')
    date_hierarchy = 'changed_at'

    def get_persian_created_at(self, obj):
        """Display Persian formatted creation date in list"""
        return obj.get_persian_created_at()
    get_persian_created_at.short_description = 'تاریخ ایجاد'
    get_persian_created_at.admin_order_field = 'created_at'

    def get_persian_changed_at(self, obj):
        """Display Persian formatted change date in list"""
        return obj.get_persian_changed_at()
    get_persian_changed_at.short_description = 'تاریخ تغییر'
    get_persian_changed_at.admin_order_field = 'changed_at'

    def get_transaction_kind_persian(self, obj):
        """Display Persian transaction kind in list"""
        if obj.transaction:
            return obj.transaction.get_kind_display()
        return '-'
    get_transaction_kind_persian.short_description = 'نوع تراکنش'
    get_transaction_kind_persian.admin_order_field = 'transaction__kind'

    def get_transaction_code(self, obj):
        """Display transaction code in list"""
        if obj.transaction:
            return obj.transaction.transaction_code
        return '-'
    get_transaction_code.short_description = 'کد تراکنش'
    get_transaction_code.admin_order_field = 'transaction__transaction_code'

    def get_transaction_amount(self, obj):
        """Display transaction amount in list"""
        if obj.transaction:
            return f"{obj.transaction.amount:,.2f}"
        return '-'
    get_transaction_amount.short_description = 'مبلغ'
    get_transaction_amount.admin_order_field = 'transaction__amount'

    def get_exchange_rate(self, obj):
        """Display exchange rate in list"""
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
    get_exchange_rate.admin_order_field = 'transaction__exchange_rate'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
