"""
Admin Module

This module provides all admin classes and configurations for the finance application.
"""

# Import base admin classes
from .base import (
    BaseAccountAdmin, BaseDepositAdmin, BaseTransactionAdmin, BaseAccountDailyBalanceAdmin
)

# Import inline classes
from .inlines import (
    AccountTxnInInline, AccountTxnOutInline, DepositTxnInInline, TransactionStateLogInline,
    AccountInline, DepositInline, TransactionInline
)

# Import mixin classes
from .mixins import (
    ReadOnlyMixin, TreasuryMixin, OperationMixin, AnalyticsMixin,
    UserManagementMixin, ProfitAccrualMixin, SnapshotMixin, DepositSnapshotMixin,
    TransactionStateMixin, TransactionActionMixin, AnalyticsActionMixin, CommonDisplayMixin
)

# Import specialized admin classes
from .user_admin import UserAdmin
from .account_admin import AccountAdmin
from .deposit_admin import DepositAdmin
from .transaction_admin import TransactionAdmin
from .transaction_state_log_admin import TransactionStateLogAdmin, TransactionStateLogInline
from .transaction_specialized_admin import (
    WithdrawalRequestAdmin, CreditIncreaseAdmin, AccountTransferAdmin,
    ProfitTransactionAdmin, DepositTransactionAdmin
)
# Financial overview functionality is now handled by supervisor.py
# User inlines are now in inlines.py

# Import admin sites
from .sites import (
    treasury_admin_site,
    operation_admin_site,
    readonly_admin_site_2
)
from .analytics import analytics_admin_site

# Import supervisor admin
from .supervisor import (
    AccountSupervisorAdmin,
    DepositSupervisorAdmin,
    register_supervisor_admin
)

# Import custom filters
from .filters import (
    ProfitCalculationFilter, FromStatePersianFilter, ToStatePersianFilter,
    AccountTypeFilter, TransactionKindFilter, TransactionStateFilter,
    AppliedFilter, DateRangeFilter
)

__all__ = [
    # Base classes
    'BaseAccountAdmin', 
    'BaseDepositAdmin',
    'BaseTransactionAdmin',
    'BaseAccountDailyBalanceAdmin',
    
    # Inline classes
    'AccountTxnInInline',
    'AccountTxnOutInline',
    'DepositTxnInInline',
    'TransactionStateLogInline',
    'AccountInline',
    'DepositInline',
    'TransactionInline',
    
    # Mixin classes
    'ReadOnlyMixin',
    'TreasuryMixin',
    'OperationMixin',
    'AnalyticsMixin',
    'UserManagementMixin',
    'ProfitAccrualMixin',
    'SnapshotMixin',
    'DepositSnapshotMixin',
    'TransactionStateMixin',
    'TransactionActionMixin',
    'AnalyticsActionMixin',
    'CommonDisplayMixin',
    
    # Specialized classes
    'UserAdmin',
    'AccountAdmin',
    'DepositAdmin',
    'TransactionAdmin',
    'TransactionStateLogAdmin',
    'WithdrawalRequestAdmin',
    'CreditIncreaseAdmin',
    'AccountTransferAdmin',
    'ProfitTransactionAdmin',
    'DepositTransactionAdmin',
    # Financial overview classes are in supervisor.py
    
    # Admin sites
    'treasury_admin_site',
    'operation_admin_site',
    'readonly_admin_site_2',
    'analytics_admin_site',
    
    # Supervisor admin
    'AccountSupervisorAdmin',
    'DepositSupervisorAdmin',
    'register_supervisor_admin',
    
    # Custom filters
    'ProfitCalculationFilter',
    'FromStatePersianFilter',
    'ToStatePersianFilter',
    'AccountTypeFilter',
    'TransactionKindFilter',
    'TransactionStateFilter',
    'AppliedFilter',
    'DateRangeFilter',
]
