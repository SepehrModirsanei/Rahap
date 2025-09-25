"""
Custom filters for admin panels

This module contains all custom filters used across different admin interfaces.
"""

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
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


class FromStatePersianFilter(SimpleListFilter):
    """Filter for transaction state logs by from_state with Persian labels"""
    title = 'از وضعیت'
    parameter_name = 'from_state'

    def lookups(self, request, model_admin):
        from ..models.transaction import Transaction
        return [(key, label) for key, label in Transaction.STATE_CHOICES]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(from_state=value)
        return queryset


class ToStatePersianFilter(SimpleListFilter):
    """Filter for transaction state logs by to_state with Persian labels"""
    title = 'به وضعیت'
    parameter_name = 'to_state'

    def lookups(self, request, model_admin):
        from ..models.transaction import Transaction
        return [(key, label) for key, label in Transaction.STATE_CHOICES]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(to_state=value)
        return queryset


class AccountTypeFilter(admin.SimpleListFilter):
    """Filter for accounts by account type"""
    title = 'نوع حساب'
    parameter_name = 'account_type'
    
    def lookups(self, request, model_admin):
        from ..models.account import Account
        return Account.ACCOUNT_TYPE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(account_type=self.value())
        return queryset


class TransactionKindFilter(admin.SimpleListFilter):
    """Filter for transactions by kind"""
    title = 'نوع تراکنش'
    parameter_name = 'kind'
    
    def lookups(self, request, model_admin):
        from ..models.transaction import Transaction
        return Transaction.KIND_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(kind=self.value())
        return queryset


class TransactionStateFilter(admin.SimpleListFilter):
    """Filter for transactions by state"""
    title = 'وضعیت تراکنش'
    parameter_name = 'state'
    
    def lookups(self, request, model_admin):
        from ..models.transaction import Transaction
        return Transaction.STATE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(state=self.value())
        return queryset


class AppliedFilter(admin.SimpleListFilter):
    """Filter for transactions by applied status"""
    title = 'وضعیت اعمال'
    parameter_name = 'applied'
    
    def lookups(self, request, model_admin):
        return (
            ('true', 'اعمال شده'),
            ('false', 'اعمال نشده'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(applied=True)
        elif self.value() == 'false':
            return queryset.filter(applied=False)
        return queryset


class DateRangeFilter(admin.SimpleListFilter):
    """Filter for date ranges"""
    title = 'بازه زمانی'
    parameter_name = 'date_range'
    
    def lookups(self, request, model_admin):
        return (
            ('today', 'امروز'),
            ('yesterday', 'دیروز'),
            ('this_week', 'این هفته'),
            ('last_week', 'هفته گذشته'),
            ('this_month', 'این ماه'),
            ('last_month', 'ماه گذشته'),
        )
    
    def queryset(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        today = now.date()
        
        if self.value() == 'today':
            return queryset.filter(created_at__date=today)
        elif self.value() == 'yesterday':
            yesterday = today - timedelta(days=1)
            return queryset.filter(created_at__date=yesterday)
        elif self.value() == 'this_week':
            start_of_week = today - timedelta(days=today.weekday())
            return queryset.filter(created_at__date__gte=start_of_week)
        elif self.value() == 'last_week':
            start_of_last_week = today - timedelta(days=today.weekday() + 7)
            end_of_last_week = start_of_last_week + timedelta(days=6)
            return queryset.filter(created_at__date__range=[start_of_last_week, end_of_last_week])
        elif self.value() == 'this_month':
            start_of_month = today.replace(day=1)
            return queryset.filter(created_at__date__gte=start_of_month)
        elif self.value() == 'last_month':
            if today.month == 1:
                start_of_last_month = today.replace(year=today.year-1, month=12, day=1)
            else:
                start_of_last_month = today.replace(month=today.month-1, day=1)
            end_of_last_month = today.replace(day=1) - timedelta(days=1)
            return queryset.filter(created_at__date__range=[start_of_last_month, end_of_last_month])
        return queryset
