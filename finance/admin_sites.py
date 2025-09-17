from django.contrib import admin
from django.contrib.admin import AdminSite
from .admin.treasury_admin import *
from .admin.operation_admin import *
from .admin.readonly_admin_1 import *
from .admin.readonly_admin_2 import *
from .admin.transaction_state_log_admin import TransactionStateLogAdmin
from .models import TransactionStateLog


# Treasury Admin Site - Full Financial Control
class TreasuryAdminSite(AdminSite):
    site_header = "Treasury Administration"
    site_title = "Treasury Admin"
    index_title = "Treasury Management"
    site_url = "/admin/treasury/"

treasury_admin_site = TreasuryAdminSite(name='treasury_admin')

# Register Treasury Admin
treasury_admin_site.register(User, TreasuryUserAdmin)
treasury_admin_site.register(Wallet, TreasuryWalletAdmin)
treasury_admin_site.register(Account, TreasuryAccountAdmin)
treasury_admin_site.register(Deposit, TreasuryDepositAdmin)
treasury_admin_site.register(Transaction, TreasuryTransactionAdmin)
treasury_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)


# Operation Admin Site - Daily Operations
class OperationAdminSite(AdminSite):
    site_header = "Operations Administration"
    site_title = "Operations Admin"
    index_title = "Daily Operations Management"
    site_url = "/admin/operations/"

operation_admin_site = OperationAdminSite(name='operation_admin')

# Register Operation Admin
operation_admin_site.register(User, OperationUserAdmin)
operation_admin_site.register(Wallet, OperationWalletAdmin)
operation_admin_site.register(Account, OperationAccountAdmin)
operation_admin_site.register(Deposit, OperationDepositAdmin)
operation_admin_site.register(Transaction, OperationTransactionAdmin)
operation_admin_site.register(TransactionStateLog, TransactionStateLogAdmin)


# Read-Only Admin Site 1 - Financial Overview
class ReadOnlyAdminSite1(AdminSite):
    site_header = "Financial Overview (Read-Only)"
    site_title = "Financial Overview"
    index_title = "Financial Data View"
    site_url = "/admin/financial-overview/"

readonly_admin_site_1 = ReadOnlyAdminSite1(name='readonly_admin_1')

# Register Read-Only Admin 1
readonly_admin_site_1.register(User, ReadOnlyUserAdmin)
readonly_admin_site_1.register(Wallet, ReadOnlyWalletAdmin)
readonly_admin_site_1.register(Account, ReadOnlyAccountAdmin)
readonly_admin_site_1.register(Deposit, ReadOnlyDepositAdmin)
readonly_admin_site_1.register(Transaction, ReadOnlyTransactionAdmin)
readonly_admin_site_1.register(AccountDailyBalance, ReadOnlyAccountDailyBalanceAdmin)


# Read-Only Admin Site 2 - Analytics & Reporting
class ReadOnlyAdminSite2(AdminSite):
    site_header = "Analytics & Reporting (Read-Only)"
    site_title = "Analytics Admin"
    index_title = "Financial Analytics & Reporting"
    site_url = "/admin/analytics/"

readonly_admin_site_2 = ReadOnlyAdminSite2(name='readonly_admin_2')

# Register Read-Only Admin 2
readonly_admin_site_2.register(User, AnalyticsUserAdmin)
readonly_admin_site_2.register(Wallet, AnalyticsWalletAdmin)
readonly_admin_site_2.register(Account, AnalyticsAccountAdmin)
readonly_admin_site_2.register(Deposit, AnalyticsDepositAdmin)
readonly_admin_site_2.register(Transaction, AnalyticsTransactionAdmin)
readonly_admin_site_2.register(AccountDailyBalance, AnalyticsAccountDailyBalanceAdmin)
