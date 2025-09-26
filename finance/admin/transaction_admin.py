from django.contrib import admin
from django.utils import timezone
from ..models import Transaction
from ..forms import TransactionAdminForm
from .inlines import TransactionStateLogInline
from .workflow import WorkflowMixin


@admin.register(Transaction)
class TransactionAdmin(WorkflowMixin, admin.ModelAdmin):
    list_display = ('transaction_code', 'id', 'user', 'kind', 'amount', 'get_source_account_display', 'get_destination_account_display', 'exchange_rate', 'state', 'get_workflow_status_display', 'get_workflow_progress', 'get_next_action_display', 'applied', 'get_receipt_display', 'get_withdrawal_destination_display', 'get_persian_scheduled_for', 'get_persian_created_at')
    list_filter = ('kind', 'state')
    search_fields = ('user__username',)
    actions = ['apply_transactions']
    form = TransactionAdminForm
    inlines = [TransactionStateLogInline]
    readonly_fields = ('transaction_code', 'get_receipt_display', 'get_withdrawal_destination_display', 'get_source_account_display', 'get_destination_account_display')
    fieldsets = (
        ('Basic Information', {
            'fields': ('transaction_code', 'user', 'kind', 'amount', 'state', 'scheduled_for')
        }),
        ('Account Information', {
            'fields': ('get_source_account_display', 'get_destination_account_display', 'destination_deposit', 'exchange_rate', 'destination_amount', 'source_price_irr', 'dest_price_irr'),
            'description': 'Source and destination accounts for the transaction'
        }),
        ('Credit Increase Details', {
            'fields': ('receipt', 'get_receipt_display'),
            'description': 'Receipt for credit increase transactions',
            'classes': ('collapse',)
        }),
        ('Withdrawal Details', {
            'fields': ('withdrawal_card_number', 'withdrawal_sheba_number', 'get_withdrawal_destination_display'),
            'description': 'Destination for withdrawal requests (either card or SHEBA)',
            'classes': ('collapse',)
        }),
        ('نظرات همه کارکنان', {
            'fields': ('user_comment', 'finance_manager_opinion', 'treasurer_opinion', 'admin_opinion'),
            'description': 'نظرات کاربر، مدیر مالی، خزانه‌دار و ادمین عملیات',
        }),
    )

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

