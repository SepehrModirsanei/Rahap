"""
Admin Site Configurations

This module contains all admin site configurations using the base classes
to eliminate duplication and provide consistent functionality.
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from .base import (
    BaseAccountAdmin, BaseDepositAdmin, BaseTransactionAdmin, BaseAccountDailyBalanceAdmin,
    ReadOnlyMixin, TreasuryMixin, OperationMixin, AnalyticsMixin
)
from .user_admin import UserAdmin
from .account_admin import AccountAdmin
from ..models import User, Account, Deposit, Transaction, AccountDailyBalance, TransactionStateLog
from ..models.transaction_proxies import (
    WithdrawalRequest, CreditIncrease, AccountTransfer, 
    ProfitTransaction, DepositTransaction
)
from .transaction_state_log_admin import TransactionStateLogAdmin
from .transaction_specialized_admin import (
    WithdrawalRequestAdmin, CreditIncreaseAdmin, AccountTransferAdmin,
    ProfitTransactionAdmin, DepositTransactionAdmin
)


# Treasury Admin Site - Full Financial Control
class TreasuryUserAdmin(TreasuryMixin, UserAdmin):
    """Treasury user admin with full permissions and inlines"""
    pass


class TreasuryAccountAdmin(TreasuryMixin, AccountAdmin):
    """Treasury account admin with full permissions and enhanced profit calculation fields"""
    pass


class TreasuryDepositAdmin(TreasuryMixin, BaseDepositAdmin):
    """Treasury deposit admin with full permissions"""
    pass


class TreasuryTransactionAdmin(TreasuryMixin, BaseTransactionAdmin):
    """Treasury transaction admin with full permissions"""
    pass


class TreasuryAccountDailyBalanceAdmin(TreasuryMixin, BaseAccountDailyBalanceAdmin):
    """Treasury account daily balance admin with full permissions"""
    pass


# Operation Admin Site - Daily Operations
class OperationUserAdmin(OperationMixin, UserAdmin):
    """Operation user admin with limited permissions and inlines"""
    pass


class OperationAccountAdmin(OperationMixin, AccountAdmin):
    """Operation account admin with limited permissions and enhanced profit calculation fields"""
    pass


class OperationDepositAdmin(OperationMixin, BaseDepositAdmin):
    """Operation deposit admin with limited permissions"""
    pass


class OperationTransactionAdmin(OperationMixin, BaseTransactionAdmin):
    """Operation transaction admin with limited permissions"""
    pass


class OperationAccountDailyBalanceAdmin(OperationMixin, BaseAccountDailyBalanceAdmin):
    """Operation account daily balance admin with limited permissions"""
    pass


# Read-Only Admin Site 1 - Financial Overview
class ReadOnlyUserAdmin(ReadOnlyMixin, UserAdmin):
    """Read-only user admin for financial overview with inlines"""
    pass


class ReadOnlyAccountAdmin(ReadOnlyMixin, AccountAdmin):
    """Read-only account admin for financial overview with enhanced profit calculation fields"""
    pass


class ReadOnlyDepositAdmin(ReadOnlyMixin, BaseDepositAdmin):
    """Read-only deposit admin for financial overview"""
    pass


class ReadOnlyTransactionAdmin(ReadOnlyMixin, BaseTransactionAdmin):
    """Read-only transaction admin for financial overview"""
    pass


class ReadOnlyAccountDailyBalanceAdmin(ReadOnlyMixin, BaseAccountDailyBalanceAdmin):
    """Read-only account daily balance admin for financial overview"""
    pass


# Read-Only Admin Site 2 - Analytics & Reporting
class AnalyticsUserAdmin(AnalyticsMixin, ReadOnlyMixin, UserAdmin):
    """Analytics user admin with enhanced display and inlines"""
    list_display = UserAdmin.list_display + ('account_count', 'transaction_count')
    
    def account_count(self, obj):
        """Display number of accounts for user"""
        return obj.accounts.count()
    account_count.short_description = 'تعداد حساب‌ها'
    
    def transaction_count(self, obj):
        """Display number of transactions for user"""
        return obj.transactions.count()
    transaction_count.short_description = 'تعداد تراکنش‌ها'


class AnalyticsAccountAdmin(AnalyticsMixin, ReadOnlyMixin, AccountAdmin):
    """Analytics account admin with enhanced display and profit calculation fields"""
    list_display = AccountAdmin.list_display + ('transaction_count', 'profit_earned')
    
    def transaction_count(self, obj):
        """Display number of transactions for account"""
        return obj.incoming_account_transactions.count() + obj.outgoing_account_transactions.count()
    transaction_count.short_description = 'تعداد تراکنش‌ها'
    
    def profit_earned(self, obj):
        """Display total profit earned"""
        profit_txns = obj.incoming_account_transactions.filter(
            kind__in=[Transaction.KIND_PROFIT_ACCOUNT, Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT]
        )
        total_profit = sum(txn.amount for txn in profit_txns)
        return f"{total_profit:,.2f}"
    profit_earned.short_description = 'سود کسب شده'


class AnalyticsDepositAdmin(AnalyticsMixin, ReadOnlyMixin, BaseDepositAdmin):
    """Analytics deposit admin with enhanced display"""
    list_display = BaseDepositAdmin.list_display + ('profit_generated', 'transaction_count')
    
    def profit_generated(self, obj):
        """Display total profit generated by deposit"""
        profit_txns = obj.incoming_deposit_transactions.filter(
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT
        )
        total_profit = sum(txn.amount for txn in profit_txns)
        return f"{total_profit:,.2f}"
    profit_generated.short_description = 'سود تولید شده'
    
    def transaction_count(self, obj):
        """Display number of transactions for deposit"""
        return obj.incoming_deposit_transactions.count()
    transaction_count.short_description = 'تعداد تراکنش‌ها'


class AnalyticsTransactionAdmin(AnalyticsMixin, ReadOnlyMixin, BaseTransactionAdmin):
    """Analytics transaction admin with enhanced display"""
    list_display = BaseTransactionAdmin.list_display + ('profit_type', 'cross_currency')
    
    def profit_type(self, obj):
        """Display if transaction is profit-related"""
        if obj.kind in [Transaction.KIND_PROFIT_ACCOUNT, Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT]:
            return "سود"
        return "عادی"
    profit_type.short_description = 'نوع تراکنش'
    
    def cross_currency(self, obj):
        """Display if transaction is cross-currency"""
        if obj.source_account and obj.destination_account:
            return obj.source_account.account_type != obj.destination_account.account_type
        return False
    cross_currency.short_description = 'ارز متقابل'
    cross_currency.boolean = True


class AnalyticsAccountDailyBalanceAdmin(AnalyticsMixin, ReadOnlyMixin, BaseAccountDailyBalanceAdmin):
    """Analytics account daily balance admin with enhanced display"""
    list_display = BaseAccountDailyBalanceAdmin.list_display + ('balance_change', 'trend')
    
    def balance_change(self, obj):
        """Display balance change from previous day"""
        # This would need to be implemented with proper logic
        return "N/A"
    balance_change.short_description = 'تغییر موجودی'
    
    def trend(self, obj):
        """Display balance trend"""
        # This would need to be implemented with proper logic
        return "N/A"
    trend.short_description = 'روند'


# Create admin sites
class TreasuryAdminSite(AdminSite):
    site_header = "مدیریت خزانه‌داری"
    site_title = "مدیریت خزانه‌داری"
    index_title = "مدیریت کامل مالی"
    site_url = "/admin/treasury/"

treasury_admin_site = TreasuryAdminSite(name='treasury_admin')

# Register Treasury Admin
treasury_admin_site.register(User, TreasuryUserAdmin)
treasury_admin_site.register(Account, TreasuryAccountAdmin)
treasury_admin_site.register(Deposit, TreasuryDepositAdmin)
treasury_admin_site.register(Transaction, TreasuryTransactionAdmin)
treasury_admin_site.register(AccountDailyBalance, TreasuryAccountDailyBalanceAdmin)
treasury_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)

# Register Specialized Transaction Admin Classes
treasury_admin_site.register(WithdrawalRequest, WithdrawalRequestAdmin)
treasury_admin_site.register(CreditIncrease, CreditIncreaseAdmin)
treasury_admin_site.register(AccountTransfer, AccountTransferAdmin)
treasury_admin_site.register(ProfitTransaction, ProfitTransactionAdmin)
treasury_admin_site.register(DepositTransaction, DepositTransactionAdmin)


class OperationAdminSite(AdminSite):
    site_header = "مدیریت عملیات"
    site_title = "مدیریت عملیات"
    index_title = "مدیریت عملیات روزانه"
    site_url = "/admin/operations/"

operation_admin_site = OperationAdminSite(name='operation_admin')

# Register Operation Admin
operation_admin_site.register(User, OperationUserAdmin)
operation_admin_site.register(Account, OperationAccountAdmin)
operation_admin_site.register(Deposit, OperationDepositAdmin)
operation_admin_site.register(Transaction, OperationTransactionAdmin)
operation_admin_site.register(AccountDailyBalance, OperationAccountDailyBalanceAdmin)
operation_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)

# Register Specialized Transaction Admin Classes
operation_admin_site.register(WithdrawalRequest, WithdrawalRequestAdmin)
operation_admin_site.register(CreditIncrease, CreditIncreaseAdmin)
operation_admin_site.register(AccountTransfer, AccountTransferAdmin)
operation_admin_site.register(ProfitTransaction, ProfitTransactionAdmin)
operation_admin_site.register(DepositTransaction, DepositTransactionAdmin)


class ReadOnlyAdminSite1(AdminSite):
    site_header = "نمای کلی مالی (فقط خواندن)"
    site_title = "نمای کلی مالی"
    index_title = "نمایش داده‌های مالی"
    site_url = "/admin/financial-overview/"

readonly_admin_site_1 = ReadOnlyAdminSite1(name='readonly_admin_1')

# Register Read-Only Admin 1
readonly_admin_site_1.register(User, ReadOnlyUserAdmin)
readonly_admin_site_1.register(Account, ReadOnlyAccountAdmin)
readonly_admin_site_1.register(Deposit, ReadOnlyDepositAdmin)
readonly_admin_site_1.register(Transaction, ReadOnlyTransactionAdmin)
readonly_admin_site_1.register(AccountDailyBalance, ReadOnlyAccountDailyBalanceAdmin)


class ReadOnlyAdminSite2(AdminSite):
    site_header = "تحلیل و گزارش‌گیری (فقط خواندن)"
    site_title = "مدیریت تحلیل"
    index_title = "تحلیل و گزارش‌گیری مالی"
    site_url = "/admin/analytics/"

readonly_admin_site_2 = ReadOnlyAdminSite2(name='readonly_admin_2')

# Register Read-Only Admin 2
readonly_admin_site_2.register(User, AnalyticsUserAdmin)
readonly_admin_site_2.register(Account, AnalyticsAccountAdmin)
readonly_admin_site_2.register(Deposit, AnalyticsDepositAdmin)
readonly_admin_site_2.register(Transaction, AnalyticsTransactionAdmin)
readonly_admin_site_2.register(AccountDailyBalance, AnalyticsAccountDailyBalanceAdmin)
