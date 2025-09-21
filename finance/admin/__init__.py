"""
Admin Module

This module provides all admin classes and configurations for the finance application.
"""

# Import base admin classes
from .base import (
    BaseUserAdmin, BaseAccountAdmin, BaseDepositAdmin, BaseTransactionAdmin, BaseAccountDailyBalanceAdmin,
    AccountTxnInInline, AccountTxnOutInline, DepositTxnInInline
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
from .user_inlines import AccountInline, DepositInline, TransactionInline

# Import admin sites
from .sites import (
    treasury_admin_site,
    operation_admin_site,
    readonly_admin_site_1,
    readonly_admin_site_2
)

# Import supervisor admin
from .supervisor import (
    AccountSupervisorAdmin,
    DepositSupervisorAdmin,
    register_supervisor_admin
)

__all__ = [
    # Base classes
    'BaseUserAdmin',
    'BaseAccountAdmin', 
    'BaseDepositAdmin',
    'BaseTransactionAdmin',
    'BaseAccountDailyBalanceAdmin',
    'AccountTxnInInline',
    'AccountTxnOutInline',
    'DepositTxnInInline',
    
    # Specialized classes
    'UserAdmin',
    'AccountAdmin',
    'DepositAdmin',
    'TransactionAdmin',
    'TransactionStateLogAdmin',
    'TransactionStateLogInline',
    'WithdrawalRequestAdmin',
    'CreditIncreaseAdmin',
    'AccountTransferAdmin',
    'ProfitTransactionAdmin',
    'DepositTransactionAdmin',
    'AccountInline',
    'DepositInline',
    'TransactionInline',
    
    # Admin sites
    'treasury_admin_site',
    'operation_admin_site',
    'readonly_admin_site_1',
    'readonly_admin_site_2',
    
    # Supervisor admin
    'AccountSupervisorAdmin',
    'DepositSupervisorAdmin',
    'register_supervisor_admin',
]
