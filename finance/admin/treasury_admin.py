from django.contrib import admin
from django.utils import timezone
from decimal import Decimal
from ..models import User, Wallet, Account, Deposit, Transaction, AccountDailyBalance
from ..forms import TransactionAdminForm


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'kind', 'amount', 'exchange_rate', 'source_wallet', 'destination_wallet', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
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


# Treasury Admin - Full Financial Control
class TreasuryUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} user(s)")
    activate_users.short_description = 'Activate selected users'

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} user(s)")
    deactivate_users.short_description = 'Deactivate selected users'


class TreasuryWalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance', 'currency', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('currency', 'created_at')
    inlines = [WalletTxnOutInline, WalletTxnInInline]
    actions = ['adjust_balance', 'freeze_wallets']

    def adjust_balance(self, request, queryset):
        # This would typically open a form for balance adjustment
        self.message_user(request, "Balance adjustment feature - implement custom form")
    adjust_balance.short_description = 'Adjust wallet balances'

    def freeze_wallets(self, request, queryset):
        # This would freeze wallets for security
        self.message_user(request, "Wallet freeze feature - implement security controls")
    freeze_wallets.short_description = 'Freeze selected wallets'


class TreasuryAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'account_type', 'balance', 'monthly_profit_rate', 'last_profit_accrual_at')
    list_filter = ('account_type', 'monthly_profit_rate')
    search_fields = ('user__username', 'name')
    actions = ['accrue_profit_now', 'snapshot_today', 'adjust_profit_rates']
    inlines = [AccountTxnOutInline, AccountTxnInInline]

    def accrue_profit_now(self, request, queryset):
        count = 0
        for account in queryset:
            before = account.balance
            account.accrue_monthly_profit()
            if account.balance != before:
                count += 1
        self.message_user(request, f"Accrued account profit for {count} item(s)")
    accrue_profit_now.short_description = 'Accrue profit now for selected accounts'

    def snapshot_today(self, request, queryset):
        today = timezone.now().date()
        created = 0
        for acc in queryset:
            obj, was_created = AccountDailyBalance.objects.get_or_create(
                account=acc, snapshot_date=today,
                defaults={'balance': Decimal(acc.balance)}
            )
            if was_created:
                created += 1
        self.message_user(request, f"Created {created} snapshot(s) for today")
    snapshot_today.short_description = 'Create today\'s snapshot for selected accounts'

    def adjust_profit_rates(self, request, queryset):
        self.message_user(request, "Profit rate adjustment feature - implement custom form")
    adjust_profit_rates.short_description = 'Adjust profit rates for selected accounts'


class TreasuryDepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'wallet', 'amount', 'monthly_profit_rate', 'last_profit_accrual_at')
    search_fields = ('user__username', 'wallet__user__username')
    list_filter = ('monthly_profit_rate', 'created_at')
    actions = ['accrue_profit_now', 'adjust_deposit_rates']
    inlines = [DepositTxnInInline]

    def accrue_profit_now(self, request, queryset):
        count = 0
        for dep in queryset:
            before = dep.last_profit_accrual_at
            dep.accrue_monthly_profit()
            if dep.last_profit_accrual_at != before:
                count += 1
        self.message_user(request, f"Accrued deposit profit for {count} item(s)")
    accrue_profit_now.short_description = 'Accrue profit now for selected deposits'

    def adjust_deposit_rates(self, request, queryset):
        self.message_user(request, "Deposit rate adjustment feature - implement custom form")
    adjust_deposit_rates.short_description = 'Adjust profit rates for selected deposits'


class TreasuryTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount', 'exchange_rate', 'state', 'applied', 'scheduled_for', 'created_at')
    list_filter = ('kind', 'state', 'applied', 'scheduled_for', 'created_at')
    search_fields = ('user__username',)
    actions = ['mark_waiting_sandogh', 'mark_verified_khazanedar', 'mark_done', 'apply_transactions', 'revert_transactions', 'bulk_schedule']
    form = TransactionAdminForm
    date_hierarchy = 'created_at'

    class Media:
        js = ('finance/transaction_admin.js',)

    def save_model(self, request, obj, form, change):
        obj.clean()
        if change:
            old_obj = Transaction.objects.get(pk=obj.pk)
            if old_obj.applied:
                old_obj.revert()
        super().save_model(request, obj, form, change)
        if not obj.scheduled_for or obj.scheduled_for <= timezone.now():
            obj.apply()

    def apply_transactions(self, request, queryset):
        applied = 0
        for txn in queryset:
            before = txn.applied
            txn.apply()
            if not before and txn.applied:
                applied += 1
        self.message_user(request, f"Applied {applied} transactions")
    apply_transactions.short_description = 'Apply selected transactions'

    def mark_waiting_sandogh(self, request, queryset):
        updated = queryset.update(state='waiting_sandogh')
        self.message_user(request, f"Moved {updated} to Waiting for Sandogh")
    mark_waiting_sandogh.short_description = 'Set state: Waiting for Sandogh'

    def mark_verified_khazanedar(self, request, queryset):
        updated = queryset.update(state='verified_khazanedar')
        self.message_user(request, f"Moved {updated} to Verified by Khazane dar")
    mark_verified_khazanedar.short_description = 'Set state: Verified by Khazane dar'

    def mark_done(self, request, queryset):
        updated = queryset.update(state='done')
        self.message_user(request, f"Moved {updated} to Done")
    mark_done.short_description = 'Set state: Done'

    def revert_transactions(self, request, queryset):
        reverted = 0
        for txn in queryset:
            if txn.applied:
                txn.revert()
                reverted += 1
        self.message_user(request, f"Reverted {reverted} transactions")
    revert_transactions.short_description = 'Revert selected transactions'

    def bulk_schedule(self, request, queryset):
        self.message_user(request, "Bulk scheduling feature - implement custom form")
    bulk_schedule.short_description = 'Bulk schedule selected transactions'
