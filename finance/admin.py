from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Wallet, Account, Deposit, Transaction, AccountDailyBalance
from .forms import TransactionAdminForm


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email')


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


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance', 'currency', 'created_at')
    search_fields = ('user__username',)
    inlines = [WalletTxnOutInline, WalletTxnInInline]


class AccountTxnOutInline(ReadOnlyTransactionInline):
    fk_name = 'source_account'


class AccountTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_account'

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'account_type', 'balance', 'monthly_profit_rate')
    list_filter = ('account_type',)
    search_fields = ('user__username', 'name')
    actions = ['accrue_profit_now', 'snapshot_today']
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
        from django.utils import timezone
        from decimal import Decimal
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


class DepositTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_deposit'

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'wallet', 'amount', 'monthly_profit_rate')
    search_fields = ('user__username', 'wallet__user__username')
    actions = ['accrue_profit_now']
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


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'amount', 'exchange_rate', 'applied', 'created_at')
    list_filter = ('kind',)
    search_fields = ('user__username',)
    actions = ['apply_transactions']
    form = TransactionAdminForm

    class Media:
        js = ('finance/transaction_admin.js',)

    def save_model(self, request, obj, form, change):
        # Validate like serializer does
        obj.clean()
        if change:
            # revert previous state before saving new values, if previously applied
            old_obj = Transaction.objects.get(pk=obj.pk)
            if old_obj.applied:
                old_obj.revert()
        super().save_model(request, obj, form, change)
        # Apply effects after saving
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
