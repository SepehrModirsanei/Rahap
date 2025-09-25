from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from ..models import User, Account, Deposit, Transaction, AccountDailyBalance, DepositDailyBalance
from .filters import ProfitCalculationFilter


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('transaction_code', 'user', 'kind', 'amount', 'exchange_rate', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'scheduled_for', 'created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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


class ReadOnlyAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'account_type', 'balance', 'monthly_profit_rate', 'last_profit_accrual_at', 'get_snapshot_count')
    list_filter = ('account_type', 'monthly_profit_rate')
    search_fields = ('user__username', 'name')
    inlines = [AccountTxnOutInline, AccountTxnInInline]
    readonly_fields = ('user', 'name', 'account_type', 'balance', 'initial_balance', 'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyDepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'initial_balance', 'monthly_profit_rate', 'last_profit_accrual_at', 'get_snapshot_count')
    search_fields = ('user__username',)
    list_filter = ('monthly_profit_rate', 'created_at')
    inlines = [DepositTxnInInline]
    readonly_fields = ('user', 'initial_balance', 'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_code', 'id', 'user', 'kind', 'amount', 'exchange_rate', 'applied', 'scheduled_for', 'created_at')
    list_filter = ('kind', 'applied', 'scheduled_for', 'created_at')
    search_fields = ('user__username',)
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'source_account', 'destination_account', 'destination_deposit', 'amount', 'kind', 'exchange_rate', 'applied', 'issued_at', 'scheduled_for', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccountDailyBalance)
class ReadOnlyAccountDailyBalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_account_name', 'get_account_type', 'get_owner', 'get_persian_snapshot_date', 'balance', 'snapshot_number')
    list_filter = ('snapshot_date', 'account__account_type')
    search_fields = ('account__user__username', 'account__name')
    readonly_fields = ('account', 'snapshot_date', 'balance')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_owner(self, obj):
        try:
            return obj.account.user
        except Exception:
            return '-'
    get_owner.short_description = 'مالک'

    def get_account_type(self, obj):
        try:
            return obj.account.get_account_type_display()
        except Exception:
            return '-'
    get_account_type.short_description = 'نوع حساب'

    def get_account_name(self, obj):
        try:
            return obj.account.name
        except Exception:
            return '-'
    get_account_name.short_description = 'نام حساب'

    def get_snapshot_total(self, obj):
        try:
            return obj.account.daily_balances.count()
        except Exception:
            return 0
    get_snapshot_total.short_description = 'تعداد اسنپ‌شات‌های حساب'


@admin.register(DepositDailyBalance)
class ReadOnlyDepositDailyBalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_deposit_name', 'get_owner_short', 'get_deposit_kind', 'get_persian_snapshot_date', 'balance', 'snapshot_number')
    list_filter = ('snapshot_date',)
    search_fields = ('deposit__user__username',)
    readonly_fields = ('deposit', 'snapshot_date', 'balance')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_deposit_kind(self, obj):
        try:
            return obj.deposit.get_profit_kind_display()
        except Exception:
            return '-'
    get_deposit_kind.short_description = 'نوع سپرده'

    def get_deposit_name(self, obj):
        try:
            return obj.deposit.user.username if not hasattr(obj.deposit, 'name') else obj.deposit.name
        except Exception:
            return '-'
    get_deposit_name.short_description = 'نام سپرده'

    def get_owner_short(self, obj):
        try:
            return obj.deposit.user.short_user_id
        except Exception:
            return '-'
    get_owner_short.short_description = 'مالک (کوتاه)'

    def get_snapshot_total(self, obj):
        try:
            return obj.deposit.daily_balances.count()
        except Exception:
            return 0
    get_snapshot_total.short_description = 'تعداد اسنپ‌شات‌های سپرده'


# Register read-only admins with the main admin site
try:
    admin.site.register(User, ReadOnlyUserAdmin)
    admin.site.register(Account, ReadOnlyAccountAdmin)
    admin.site.register(Deposit, ReadOnlyDepositAdmin)
    admin.site.register(Transaction, ReadOnlyTransactionAdmin)
    admin.site.register(AccountDailyBalance, ReadOnlyAccountDailyBalanceAdmin)
    admin.site.register(DepositDailyBalance, ReadOnlyDepositDailyBalanceAdmin)
except AlreadyRegistered:
    pass