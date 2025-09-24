from django.contrib import admin
from ..models import Deposit, Transaction
from ..forms import DepositAdminForm
from .filters import ProfitCalculationFilter


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'kind', 'amount', 'exchange_rate', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


class DepositTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_deposit'


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    form = DepositAdminForm
    list_display = ('id', 'user', 'initial_balance', 'monthly_profit_rate', 'profit_kind', 'breakage_coefficient', 'get_persian_created_at', 'get_profit_calculation_info')
    list_filter = (ProfitCalculationFilter,)
    search_fields = ('user__username',)
    actions = ['accrue_profit_now']
    inlines = [DepositTxnInInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'initial_balance', 'monthly_profit_rate', 'profit_kind', 'breakage_coefficient'),
            'description': 'All deposits start with zero balance. Use transactions to add money to deposits.'
        }),
    )

    def accrue_profit_now(self, request, queryset):
        count = 0
        for dep in queryset:
            before = dep.last_profit_accrual_at
            dep.accrue_monthly_profit()
            if dep.last_profit_accrual_at != before:
                count += 1
        self.message_user(request, f"Accrued deposit profit for {count} item(s)")
    accrue_profit_now.short_description = 'Accrue profit now for selected deposits'
