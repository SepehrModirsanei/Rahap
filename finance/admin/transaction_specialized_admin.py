from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from ..models import Transaction
from ..models.transaction_proxies import (
    WithdrawalRequest, CreditIncrease, AccountTransfer, 
    ProfitTransaction, DepositTransaction
)
from ..forms import TransactionAdminForm
from ..forms.specialized_forms import (
    WithdrawalRequestForm, CreditIncreaseForm, AccountTransferForm,
    ProfitTransactionForm, DepositTransactionForm
)
from .transaction_state_log_admin import TransactionStateLogInline


class BaseTransactionAdmin(admin.ModelAdmin):
    """Base admin class for all transaction types"""
    form = TransactionAdminForm
    
    def add_view(self, request, form_url='', extra_context=None):
        """Override add_view to include Persian date picker template"""
        extra_context = extra_context or {}
        extra_context['include_persian_datepicker'] = True
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change_view to include Persian date picker template"""
        extra_context = extra_context or {}
        extra_context['include_persian_datepicker'] = True
        return super().change_view(request, object_id, form_url, extra_context)
    inlines = [TransactionStateLogInline]
    readonly_fields = ('get_persian_created_at',)
    
    class Media:
        js = ('finance/transaction_admin.js',)

    def save_model(self, request, obj, form, change):
        # Validate like serializer does
        obj.clean()
        if change:
            # revert previous state before saving new values, if previously applied
            old_obj = Transaction.objects.get(pk=obj.pk)
            if old_obj.applied:
                old_obj.revert()
        # Track who made the change
        obj._changed_by = request.user
        super().save_model(request, obj, form, change)
        # Apply effects after saving
        # Only auto-apply if not scheduled in the future
        if not obj.scheduled_for or obj.scheduled_for <= timezone.now():
            obj.apply()

    def apply_transactions(self, request, queryset):
        applied = 0
        for txn in queryset:
            before = txn.applied
            txn.apply()
            if not before and txn.applied:
                applied += 1
        self.message_user(request, f"Applied {applied} transactions")
    apply_transactions.short_description = 'Apply selected transactions'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(BaseTransactionAdmin):
    """Admin for withdrawal request transactions"""
    form = WithdrawalRequestForm
    list_display = ('id', 'user', 'source_account', 'amount', 'state', 'applied', 'get_withdrawal_destination_display', 'get_persian_scheduled_for', 'get_persian_created_at')
    list_filter = ('state', 'applied', 'issued_at')
    search_fields = ('user__username', 'user__user_id', 'source_account__name')
    actions = ['apply_transactions']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind=Transaction.KIND_WITHDRAWAL_REQUEST)


@admin.register(CreditIncrease)
class CreditIncreaseAdmin(BaseTransactionAdmin):
    """Admin for credit increase transactions"""
    form = CreditIncreaseForm
    list_display = ('id', 'user', 'destination_account', 'amount', 'state', 'applied', 'get_receipt_display', 'get_persian_scheduled_for', 'get_persian_created_at')
    list_filter = ('state', 'applied', 'issued_at')
    search_fields = ('user__username', 'user__user_id', 'destination_account__name')
    actions = ['apply_transactions']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind=Transaction.KIND_CREDIT_INCREASE)


@admin.register(AccountTransfer)
class AccountTransferAdmin(BaseTransactionAdmin):
    """Admin for account-to-account transfer transactions"""
    form = AccountTransferForm
    list_display = ('id', 'user', 'source_account', 'destination_account', 'amount', 'exchange_rate', 'state', 'applied', 'get_persian_created_at')
    list_filter = ('state', 'applied', 'issued_at')
    search_fields = ('user__username', 'user__user_id', 'source_account__name', 'destination_account__name')
    actions = ['apply_transactions']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT)


@admin.register(ProfitTransaction)
class ProfitTransactionAdmin(BaseTransactionAdmin):
    """Admin for profit-related transactions"""
    form = ProfitTransactionForm
    list_display = ('id', 'user', 'destination_account', 'amount', 'state', 'applied', 'get_persian_created_at')
    list_filter = ('state', 'applied', 'issued_at')
    search_fields = ('user__username', 'user__user_id', 'destination_account__name')
    actions = ['apply_transactions']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            kind__in=[
                Transaction.KIND_PROFIT_ACCOUNT,
                Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT
            ]
        )


@admin.register(DepositTransaction)
class DepositTransactionAdmin(BaseTransactionAdmin):
    """Admin for account-to-deposit transactions"""
    form = DepositTransactionForm
    list_display = ('id', 'user', 'source_account', 'destination_deposit', 'amount', 'state', 'applied', 'get_persian_created_at')
    list_filter = ('state', 'applied', 'issued_at')
    search_fields = ('user__username', 'user__user_id', 'source_account__name', 'destination_deposit__user__username')
    actions = ['apply_transactions']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL)
