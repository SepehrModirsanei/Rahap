from django.contrib import admin
from django.utils import timezone
from ..models import Transaction
from ..forms import TransactionAdminForm


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount', 'exchange_rate', 'state', 'applied', 'scheduled_for', 'created_at')
    list_filter = ('kind', 'state')
    search_fields = ('user__username',)
    actions = ['apply_transactions']
    form = TransactionAdminForm

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
