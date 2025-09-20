"""
Custom filters for admin panels
"""
from django.contrib import admin
from django.db import models


class ProfitCalculationFilter(admin.SimpleListFilter):
    """Filter for accounts/deposits based on profit calculation status"""
    title = 'محاسبه سود'
    parameter_name = 'profit_calculation'
    
    def lookups(self, request, model_admin):
        return (
            ('active', 'فعال (سود محاسبه شده)'),
            ('inactive', 'غیرفعال (سود محاسبه نشده)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(last_profit_accrual_at__isnull=False)
        elif self.value() == 'inactive':
            return queryset.filter(last_profit_accrual_at__isnull=True)
        return queryset
