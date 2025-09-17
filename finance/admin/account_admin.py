from django.contrib import admin
from django.utils import timezone
from decimal import Decimal
from ..models import Account, Transaction, AccountDailyBalance


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('user', 'kind', 'amount', 'exchange_rate', 'source_wallet', 'destination_wallet', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


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
