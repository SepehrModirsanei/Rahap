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
from .workflow import (
    TreasuryWorkflowTransactionAdmin, OperationWorkflowTransactionAdmin,
    SupervisorWorkflowTransactionAdmin, FinanceManagerWorkflowTransactionAdmin
)
from .user_admin import UserAdmin
from .account_admin import AccountAdmin
from .analytics import analytics_admin_site
from .authentication import (
    TreasuryAdminSite, FinanceManagerAdminSite, OperationAdminSite,
    SupervisorAdminSite, AnalyticsAdminSite
)
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


# Create authenticated admin sites
treasury_admin_site = TreasuryAdminSite()

# Register Treasury Admin with TreasuryMixin applied dynamically
treasury_admin_site.register(User, type('TreasuryUserAdmin', (TreasuryMixin, UserAdmin), {}))
treasury_admin_site.register(Account, type('TreasuryAccountAdmin', (TreasuryMixin, AccountAdmin), {}))
treasury_admin_site.register(Deposit, type('TreasuryDepositAdmin', (TreasuryMixin, BaseDepositAdmin), {}))
treasury_admin_site.register(AccountDailyBalance, type('TreasuryAccountDailyBalanceAdmin', (TreasuryMixin, BaseAccountDailyBalanceAdmin), {}))
treasury_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)

# Register Treasury Admin with Workflow Transaction Admin
treasury_admin_site.register(Transaction, TreasuryWorkflowTransactionAdmin)

# Register Specialized Transaction Admin Classes
treasury_admin_site.register(WithdrawalRequest, WithdrawalRequestAdmin)
treasury_admin_site.register(CreditIncrease, CreditIncreaseAdmin)
treasury_admin_site.register(AccountTransfer, AccountTransferAdmin)
treasury_admin_site.register(ProfitTransaction, ProfitTransactionAdmin)
treasury_admin_site.register(DepositTransaction, DepositTransactionAdmin)


operation_admin_site = OperationAdminSite()

# Register Operation Admin with OperationMixin applied dynamically
operation_admin_site.register(User, type('OperationUserAdmin', (OperationMixin, UserAdmin), {}))
operation_admin_site.register(Account, type('OperationAccountAdmin', (OperationMixin, AccountAdmin), {}))
operation_admin_site.register(Deposit, type('OperationDepositAdmin', (OperationMixin, BaseDepositAdmin), {}))
operation_admin_site.register(AccountDailyBalance, type('OperationAccountDailyBalanceAdmin', (OperationMixin, BaseAccountDailyBalanceAdmin), {}))
operation_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)

# Register Operation Admin with Workflow Transaction Admin
operation_admin_site.register(Transaction, OperationWorkflowTransactionAdmin)

# Register Specialized Transaction Admin Classes
operation_admin_site.register(WithdrawalRequest, WithdrawalRequestAdmin)
operation_admin_site.register(CreditIncrease, CreditIncreaseAdmin)
operation_admin_site.register(AccountTransfer, AccountTransferAdmin)
operation_admin_site.register(ProfitTransaction, ProfitTransactionAdmin)
operation_admin_site.register(DepositTransaction, DepositTransactionAdmin)


# Finance Manager Admin Site
finance_manager_admin_site = FinanceManagerAdminSite()

# Register Finance Manager Admin with workflow
finance_manager_admin_site.register(User, type('FinanceManagerUserAdmin', (ReadOnlyMixin, UserAdmin), {}))
finance_manager_admin_site.register(Account, type('FinanceManagerAccountAdmin', (ReadOnlyMixin, AccountAdmin), {}))
finance_manager_admin_site.register(Deposit, type('FinanceManagerDepositAdmin', (ReadOnlyMixin, BaseDepositAdmin), {}))
finance_manager_admin_site.register(Transaction, FinanceManagerWorkflowTransactionAdmin)
finance_manager_admin_site.register(AccountDailyBalance, type('FinanceManagerAccountDailyBalanceAdmin', (ReadOnlyMixin, BaseAccountDailyBalanceAdmin), {}))
finance_manager_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)

# Register Specialized Transaction Admin Classes for Finance Manager
finance_manager_admin_site.register(WithdrawalRequest, WithdrawalRequestAdmin)
finance_manager_admin_site.register(CreditIncrease, CreditIncreaseAdmin)
finance_manager_admin_site.register(AccountTransfer, AccountTransferAdmin)
finance_manager_admin_site.register(ProfitTransaction, ProfitTransactionAdmin)
finance_manager_admin_site.register(DepositTransaction, DepositTransactionAdmin)

# Sandogh functionality is now part of Treasury Admin

# Financial Overview is now handled by supervisor.py
# Use supervisor admin classes for financial overview functionality

# Use the analytics admin site from analytics.py which has the custom dashboard
# Analytics admin site is already created and registered in analytics.py

# Supervisor Admin Site
supervisor_admin_site = SupervisorAdminSite()

# Register Supervisor Admin with read-only access
from .supervisor import register_supervisor_admin
register_supervisor_admin(supervisor_admin_site)

# Expose analytics admin site under the canonical name
analytics_admin_site = analytics_admin_site