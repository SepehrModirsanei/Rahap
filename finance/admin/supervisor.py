"""
Supervisor Admin Classes

This module contains admin classes for supervisor/oversight functionality.
"""

from django.contrib import admin
from ..models import Account, Deposit
from .base import ReadOnlyMixin, BaseAccountAdmin, BaseDepositAdmin
from ..utils import get_persian_date_display


class AccountSupervisorAdmin(ReadOnlyMixin, BaseAccountAdmin):
    """Supervisor admin for Account model with oversight functionality"""
    list_display = ('id', 'user', 'name', 'account_type', 'initial_balance', 'balance_display', 'monthly_profit_rate', 'created_at_display')
    list_filter = ('account_type', 'created_at')
    search_fields = ('user__username', 'name')
    
    def get_queryset(self, request):
        """Override to add supervisor-specific filtering if needed"""
        return super().get_queryset(request)


class DepositSupervisorAdmin(ReadOnlyMixin, BaseDepositAdmin):
    """Supervisor admin for Deposit model with oversight functionality"""
    list_display = ('id', 'user', 'initial_balance', 'monthly_profit_rate', 'balance_display', 'last_profit_accrual_at_display')
    search_fields = ('user__username',)
    
    def last_profit_accrual_at_display(self, obj):
        """Display Persian date for last profit accrual"""
        if obj.last_profit_accrual_at:
            return get_persian_date_display(obj.last_profit_accrual_at)
        return '-'
    last_profit_accrual_at_display.short_description = 'آخرین سود'


def register_supervisor_admin(site: admin.AdminSite):
    """Register supervisor admin classes with a site"""
    site.register(Account, AccountSupervisorAdmin)
    site.register(Deposit, DepositSupervisorAdmin)
