"""
Admin Site Configurations

This module contains all admin site configurations using dynamic class creation
to eliminate duplication and provide consistent functionality.
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from .base import (
    BaseAccountAdmin, BaseDepositAdmin, BaseTransactionAdmin, BaseAccountDailyBalanceAdmin
)
from .mixins import ReadOnlyMixin, TreasuryMixin, OperationMixin
from .user_admin import UserAdmin
from .account_admin import AccountAdmin
from .analytics import analytics_admin_site
from ..models import User, Account, Deposit, Transaction, AccountDailyBalance, DepositDailyBalance, TransactionStateLog
from ..models.transaction_proxies import (
    WithdrawalRequest, CreditIncrease, AccountTransfer, 
    ProfitTransaction, DepositTransaction
)
from .transaction_state_log_admin import TransactionStateLogAdmin
from .transaction_specialized_admin import (
    WithdrawalRequestAdmin, CreditIncreaseAdmin, AccountTransferAdmin,
    ProfitTransactionAdmin, DepositTransactionAdmin
)


# Create admin sites
class TreasuryAdminSite(AdminSite):
    site_header = "مدیریت خزانه‌داری"
    site_title = "مدیریت خزانه‌داری"
    index_title = "مدیریت کامل مالی"
    site_url = "/admin/treasury/"

treasury_admin_site = TreasuryAdminSite(name='treasury_admin')

# Register Treasury Admin with TreasuryMixin applied dynamically
treasury_admin_site.register(User, type('TreasuryUserAdmin', (TreasuryMixin, UserAdmin), {}))
treasury_admin_site.register(Account, type('TreasuryAccountAdmin', (TreasuryMixin, AccountAdmin), {}))
treasury_admin_site.register(Deposit, type('TreasuryDepositAdmin', (TreasuryMixin, BaseDepositAdmin), {}))
treasury_admin_site.register(Transaction, type('TreasuryTransactionAdmin', (TreasuryMixin, BaseTransactionAdmin), {}))
treasury_admin_site.register(AccountDailyBalance, type('TreasuryAccountDailyBalanceAdmin', (TreasuryMixin, BaseAccountDailyBalanceAdmin), {}))
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

# Register Operation Admin with OperationMixin applied dynamically
operation_admin_site.register(User, type('OperationUserAdmin', (OperationMixin, UserAdmin), {}))
operation_admin_site.register(Account, type('OperationAccountAdmin', (OperationMixin, AccountAdmin), {}))
operation_admin_site.register(Deposit, type('OperationDepositAdmin', (OperationMixin, BaseDepositAdmin), {}))
operation_admin_site.register(Transaction, type('OperationTransactionAdmin', (OperationMixin, BaseTransactionAdmin), {}))
operation_admin_site.register(AccountDailyBalance, type('OperationAccountDailyBalanceAdmin', (OperationMixin, BaseAccountDailyBalanceAdmin), {}))
operation_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)

# Register Specialized Transaction Admin Classes
operation_admin_site.register(WithdrawalRequest, WithdrawalRequestAdmin)
operation_admin_site.register(CreditIncrease, CreditIncreaseAdmin)
operation_admin_site.register(AccountTransfer, AccountTransferAdmin)
operation_admin_site.register(ProfitTransaction, ProfitTransactionAdmin)
operation_admin_site.register(DepositTransaction, DepositTransactionAdmin)


# Financial Overview is now handled by supervisor.py
# Use supervisor admin classes for financial overview functionality

# Use the analytics admin site from analytics.py which has the custom dashboard
# Analytics admin site is already created and registered in analytics.py

# For backward compatibility
readonly_admin_site_2 = analytics_admin_site