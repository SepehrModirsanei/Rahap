from django.contrib import admin
from django.utils import timezone
from decimal import Decimal
from ..models import User, Account, Deposit, Transaction, AccountDailyBalance, DepositDailyBalance
from ..forms import TransactionAdminForm
from .transaction_state_log_admin import TransactionStateLogInline


class ReadOnlyTransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('transaction_code', 'user', 'kind', 'amount', 'exchange_rate', 'source_account', 'destination_account', 'destination_deposit', 'applied', 'get_persian_created_at')
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


class AccountTxnOutInline(ReadOnlyTransactionInline):
    fk_name = 'source_account'


class AccountTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_account'


class DepositTxnInInline(ReadOnlyTransactionInline):
    fk_name = 'destination_deposit'


# Operation Admin - Daily Operations Management
class OperationUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    readonly_fields = ('is_superuser', 'is_staff', 'date_joined', 'last_login')
    fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} user(s)")
    activate_users.short_description = 'Activate selected users'

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} user(s)")
    deactivate_users.short_description = 'Deactivate selected users'


class OperationAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'account_type', 'balance', 'monthly_profit_rate')
    list_filter = ('account_type',)
    search_fields = ('user__username', 'name')
    actions = ['accrue_profit_now', 'snapshot_today']
    inlines = [AccountTxnOutInline, AccountTxnInInline]
    readonly_fields = ('created_at', 'updated_at', 'last_profit_accrual_at')

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


class OperationDepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'initial_balance', 'monthly_profit_rate')
    search_fields = ('user__username',)
    actions = ['accrue_profit_now']
    inlines = [DepositTxnInInline]
    readonly_fields = ('created_at', 'updated_at', 'last_profit_accrual_at')

    def accrue_profit_now(self, request, queryset):
        count = 0
        for dep in queryset:
            before = dep.last_profit_accrual_at
            dep.accrue_monthly_profit()
            if dep.last_profit_accrual_at != before:
                count += 1
        self.message_user(request, f"Accrued deposit profit for {count} item(s)")
    accrue_profit_now.short_description = 'Accrue profit now for selected deposits'


class OperationTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_code', 'id', 'user', 'kind', 'amount', 'state', 'applied', 'get_persian_scheduled_for', 'get_persian_created_at')
    list_filter = ('kind', 'state', 'applied', 'created_at')
    search_fields = ('user__username',)
    actions = ['submit_to_treasury', 'advance_state', 'mark_rejected', 'mark_waiting_finance_manager', 'apply_transactions', 'view_transaction_summary']
    form = TransactionAdminForm
    inlines = [TransactionStateLogInline]
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'issued_at')

    class Media:
        js = ('finance/transaction_admin.js',)

    def save_model(self, request, obj, form, change):
        obj.clean()
        if change:
            old_obj = Transaction.objects.get(pk=obj.pk)
            if old_obj.applied:
                old_obj.revert()
        # Track who made the change
        obj._changed_by = request.user
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

    def submit_to_treasury(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.state != 'waiting_treasury':
                txn.state = 'waiting_treasury'
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Submitted {moved} to Treasury")
    submit_to_treasury.short_description = 'Set state: Waiting for Treasury'

    def advance_state(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.advance_state():
                moved += 1
        self.message_user(request, f"Advanced {moved} transaction(s) to next state")
    advance_state.short_description = 'Advance to next state'

    def mark_rejected(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.state != 'rejected':
                txn.state = 'rejected'
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Moved {moved} to Rejected")
    mark_rejected.short_description = 'Set state: Rejected'

    def mark_waiting_finance_manager(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.state != 'waiting_finance_manager':
                txn.state = 'waiting_finance_manager'
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Moved {moved} to Waiting for Finance Manager")
    mark_waiting_finance_manager.short_description = 'Set state: Waiting for Finance Manager'

    def view_transaction_summary(self, request, queryset):
        total_amount = sum(float(t.amount) for t in queryset)
        applied_count = queryset.filter(applied=True).count()
        self.message_user(request, f"Total amount: {total_amount:,.2f}, Applied: {applied_count}/{queryset.count()}")
    view_transaction_summary.short_description = 'View transaction summary'
