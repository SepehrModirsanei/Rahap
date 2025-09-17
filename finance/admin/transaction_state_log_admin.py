from django.contrib import admin
from ..models import TransactionStateLog


class TransactionStateLogInline(admin.TabularInline):
    model = TransactionStateLog
    extra = 0
    can_delete = False
    readonly_fields = ('from_state', 'to_state', 'changed_by', 'changed_at', 'notes')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TransactionStateLog)
class TransactionStateLogAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'from_state', 'to_state', 'changed_by', 'changed_at')
    list_filter = ('to_state', 'changed_at', 'changed_by')
    search_fields = ('transaction__id', 'transaction__user__username', 'changed_by__username')
    readonly_fields = ('transaction', 'from_state', 'to_state', 'changed_by', 'changed_at', 'notes')
    date_hierarchy = 'changed_at'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
