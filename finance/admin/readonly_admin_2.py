from django.contrib import admin
from ..models import User, Account, Deposit, Transaction, AccountDailyBalance, DepositDailyBalance


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'kind', 'amount', 'exchange_rate', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'created_at')
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


# Read-Only Admin Panel 2 - Analytics & Reporting
class AnalyticsUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    readonly_fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    actions = ['export_user_data']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def export_user_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} users")
    export_user_data.short_description = 'Export user data'


class AnalyticsAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'account_type', 'balance', 'monthly_profit_rate', 'last_profit_accrual_at')
    list_filter = ('account_type', 'monthly_profit_rate')
    search_fields = ('user__username', 'name')
    inlines = [AccountTxnOutInline, AccountTxnInInline]
    readonly_fields = ('user', 'name', 'account_type', 'balance', 'initial_balance', 'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at')
    actions = ['calculate_profit_summary', 'export_account_data']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def calculate_profit_summary(self, request, queryset):
        total_balance = sum(float(a.balance) for a in queryset)
        avg_rate = sum(float(a.monthly_profit_rate) for a in queryset) / queryset.count() if queryset.count() > 0 else 0
        self.message_user(request, f"Total balance: {total_balance:,.2f}, Average rate: {avg_rate:.2f}%")
    calculate_profit_summary.short_description = 'Calculate profit summary'

    def export_account_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} accounts")
    export_account_data.short_description = 'Export account data'


class AnalyticsDepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'initial_balance', 'monthly_profit_rate', 'last_profit_accrual_at')
    search_fields = ('user__username',)
    list_filter = ('monthly_profit_rate', 'created_at')
    inlines = [DepositTxnInInline]
    readonly_fields = ('user', 'initial_balance', 'monthly_profit_rate', 'last_profit_accrual_at', 'created_at', 'updated_at')
    actions = ['calculate_deposit_summary', 'export_deposit_data']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def calculate_deposit_summary(self, request, queryset):
        total_amount = sum(float(d.amount) for d in queryset)
        avg_rate = sum(float(d.monthly_profit_rate) for d in queryset) / queryset.count() if queryset.count() > 0 else 0
        self.message_user(request, f"Total deposits: {total_amount:,.2f}, Average rate: {avg_rate:.2f}%")
    calculate_deposit_summary.short_description = 'Calculate deposit summary'

    def export_deposit_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} deposits")
    export_deposit_data.short_description = 'Export deposit data'


class AnalyticsTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount', 'exchange_rate', 'applied', 'scheduled_for', 'created_at')
    list_filter = ('kind', 'applied', 'scheduled_for', 'created_at')
    search_fields = ('user__username',)
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'source_account', 'destination_account', 'destination_deposit', 'amount', 'kind', 'exchange_rate', 'applied', 'issued_at', 'scheduled_for', 'created_at')
    actions = ['calculate_transaction_summary', 'export_transaction_data']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def calculate_transaction_summary(self, request, queryset):
        total_amount = sum(float(t.amount) for t in queryset)
        applied_count = queryset.filter(applied=True).count()
        pending_count = queryset.filter(applied=False).count()
        self.message_user(request, f"Total amount: {total_amount:,.2f}, Applied: {applied_count}, Pending: {pending_count}")
    calculate_transaction_summary.short_description = 'Calculate transaction summary'

    def export_transaction_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} transactions")
    export_transaction_data.short_description = 'Export transaction data'


class AnalyticsAccountDailyBalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'snapshot_date', 'balance')
    list_filter = ('snapshot_date', 'account__account_type')
    search_fields = ('account__user__username', 'account__name')
    readonly_fields = ('account', 'snapshot_date', 'balance')
    actions = ['calculate_balance_trend', 'export_balance_data']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def calculate_balance_trend(self, request, queryset):
        self.message_user(request, f"Calculating balance trend for {queryset.count()} records")
    calculate_balance_trend.short_description = 'Calculate balance trend'

    def export_balance_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} balance records")
    export_balance_data.short_description = 'Export balance data'


class AnalyticsDepositDailyBalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'deposit', 'get_persian_snapshot_date', 'balance')
    list_filter = ('snapshot_date',)
    search_fields = ('deposit__user__username',)
    readonly_fields = ('deposit', 'snapshot_date', 'balance')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
