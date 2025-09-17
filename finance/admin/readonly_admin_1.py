from django.contrib import admin
from ..models import User, Wallet, Account, Deposit, Transaction, AccountDailyBalance


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'kind', 'amount', 'exchange_rate', 'source_wallet', 'destination_wallet', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class WalletTxnOutInline(ReadOnlyTransactionInline):
    fk_name = 'source_wallet'


class WalletTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_wallet'


class AccountTxnOutInline(ReadOnlyTransactionInline):
    fk_name = 'source_account'


class AccountTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_account'


class DepositTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_deposit'


# Read-Only Admin Panel 1 - Financial Overview
class ReadOnlyUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    readonly_fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'date_joined')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyWalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance', 'currency', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('currency', 'created_at')
    inlines = [WalletTxnOutInline, WalletTxnInInline]
    readonly_fields = ('user', 'balance', 'currency', 'created_at', 'updated_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'account_type', 'balance', 'monthly_profit_rate', 'last_profit_accrual_at')
    list_filter = ('account_type', 'monthly_profit_rate')
    search_fields = ('user__username', 'name')
    inlines = [AccountTxnOutInline, AccountTxnInInline]
    readonly_fields = ('user', 'wallet', 'name', 'account_type', 'balance', 'initial_balance', 'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyDepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'wallet', 'amount', 'monthly_profit_rate', 'last_profit_accrual_at')
    search_fields = ('user__username', 'wallet__user__username')
    list_filter = ('monthly_profit_rate', 'created_at')
    inlines = [DepositTxnInInline]
    readonly_fields = ('user', 'wallet', 'amount', 'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount', 'exchange_rate', 'applied', 'scheduled_for', 'created_at')
    list_filter = ('kind', 'applied', 'scheduled_for', 'created_at')
    search_fields = ('user__username',)
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'source_wallet', 'destination_wallet', 'source_account', 'destination_account', 'destination_deposit', 'amount', 'kind', 'exchange_rate', 'applied', 'issued_at', 'scheduled_for', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyAccountDailyBalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'snapshot_date', 'balance')
    list_filter = ('snapshot_date', 'account__account_type')
    search_fields = ('account__user__username', 'account__name')
    readonly_fields = ('account', 'snapshot_date', 'balance')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
