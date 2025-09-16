from django.contrib import admin
from .models import Account, Deposit


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AccountSupervisorAdmin(ReadOnlyAdmin):
    list_display = ('id', 'user', 'name', 'account_type', 'initial_balance', 'balance', 'monthly_profit_rate', 'created_at')
    list_filter = ('account_type',)
    search_fields = ('user__username', 'name')


class DepositSupervisorAdmin(ReadOnlyAdmin):
    list_display = ('id', 'user', 'wallet', 'amount', 'monthly_profit_rate', 'last_profit_accrual_at')
    search_fields = ('user__username', 'wallet__user__username')


def register(site: admin.AdminSite):
    site.register(Account, AccountSupervisorAdmin)
    site.register(Deposit, DepositSupervisorAdmin)


