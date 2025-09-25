from django.contrib import admin
from ..models import Deposit, Transaction
from ..forms import DepositAdminForm
from .filters import ProfitCalculationFilter
from .inlines import DepositTxnInInline
from .mixins import ProfitAccrualMixin


# All inline classes are now imported from inlines.py


@admin.register(Deposit)
class DepositAdmin(ProfitAccrualMixin, admin.ModelAdmin):
    form = DepositAdminForm
    list_display = ('id', 'user', 'get_kind', 'get_unit', 'initial_balance', 'monthly_profit_rate', 'profit_kind', 'breakage_coefficient', 'get_snapshot_count', 'get_persian_created_at', 'get_profit_calculation_info')
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
