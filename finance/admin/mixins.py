"""
Admin Mixin Classes

This module contains all mixin classes for the finance application.
Mixins provide reusable functionality that can be added to any admin class.
"""

from django.contrib import admin
from django.utils import timezone
from decimal import Decimal
from ..models import AccountDailyBalance, DepositDailyBalance


class ReadOnlyMixin:
    """Mixin for read-only admin classes"""
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class TreasuryMixin:
    """Mixin for treasury admin classes with full permissions"""
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class OperationMixin:
    """Mixin for operation admin classes with limited permissions"""
    
    def has_add_permission(self, request):
        return request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        return False  # Operations staff cannot delete


class AnalyticsMixin:
    """Mixin for analytics admin classes with enhanced display"""
    
    def get_queryset(self, request):
        """Override to add analytics-specific filtering"""
        return super().get_queryset(request)
    
    def changelist_view(self, request, extra_context=None):
        """Add analytics context to changelist"""
        extra_context = extra_context or {}
        extra_context['analytics_mode'] = True
        return super().changelist_view(request, extra_context)


class UserManagementMixin:
    """Mixin for user management actions"""
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} user(s)")
    activate_users.short_description = 'Activate selected users'

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} user(s)")
    deactivate_users.short_description = 'Deactivate selected users'


class ProfitAccrualMixin:
    """Mixin for profit accrual actions"""
    
    def accrue_profit_now(self, request, queryset):
        count = 0
        for obj in queryset:
            before = obj.balance
            obj.accrue_monthly_profit()
            if obj.balance != before:
                count += 1
        self.message_user(request, f"Accrued profit for {count} item(s)")
    accrue_profit_now.short_description = 'Accrue profit now for selected items'


class SnapshotMixin:
    """Mixin for snapshot creation actions"""
    
    def snapshot_today(self, request, queryset):
        today = timezone.now().date()
        created = 0
        for obj in queryset:
            obj, was_created = AccountDailyBalance.objects.get_or_create(
                account=obj, snapshot_date=today,
                defaults={'balance': Decimal(obj.balance)}
            )
            if was_created:
                created += 1
        self.message_user(request, f"Created {created} snapshot(s) for today")
    snapshot_today.short_description = 'Create today\'s snapshot for selected items'


class DepositSnapshotMixin:
    """Mixin for deposit snapshot creation actions"""
    
    def snapshot_today(self, request, queryset):
        today = timezone.now().date()
        created = 0
        for obj in queryset:
            obj, was_created = DepositDailyBalance.objects.get_or_create(
                deposit=obj, snapshot_date=today,
                defaults={'balance': Decimal(obj.balance)}
            )
            if was_created:
                created += 1
        self.message_user(request, f"Created {created} snapshot(s) for today")
    snapshot_today.short_description = 'Create today\'s snapshot for selected deposits'


class TransactionStateMixin:
    """Mixin for transaction state management actions"""
    
    def mark_waiting_sandogh(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.state != 'waiting_sandogh':
                txn.state = 'waiting_sandogh'
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Moved {moved} to Waiting for Sandogh")
    mark_waiting_sandogh.short_description = 'Set state: Waiting for Sandogh'

    def mark_verified_khazanedar(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.state != 'verified_khazanedar':
                txn.state = 'verified_khazanedar'
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Moved {moved} to Verified by Khazane dar")
    mark_verified_khazanedar.short_description = 'Set state: Verified by Khazane dar'

    def mark_done(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.state != 'done':
                txn.state = 'done'
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Moved {moved} to Done")
    mark_done.short_description = 'Set state: Done'

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

    def advance_state(self, request, queryset):
        moved = 0
        for txn in queryset:
            if txn.advance_state():
                moved += 1
        self.message_user(request, f"Advanced {moved} transaction(s) to next state")
    advance_state.short_description = 'Advance to next state'

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


class TransactionActionMixin:
    """Mixin for transaction action operations"""
    
    def apply_transactions(self, request, queryset):
        applied = 0
        for txn in queryset:
            before = txn.applied
            txn.apply()
            if not before and txn.applied:
                applied += 1
        self.message_user(request, f"Applied {applied} transactions")
    apply_transactions.short_description = 'Apply selected transactions'

    def revert_transactions(self, request, queryset):
        reverted = 0
        for txn in queryset:
            if txn.applied:
                txn.revert()
                reverted += 1
        self.message_user(request, f"Reverted {reverted} transactions")
    revert_transactions.short_description = 'Revert selected transactions'



class CommonDisplayMixin:
    """Mixin for common display methods used across admin classes"""
    
    def balance_display(self, obj):
        """Display balance with formatting"""
        return f"{obj.balance:,.2f}"
    balance_display.short_description = 'موجودی'
    
    def created_at_display(self, obj):
        """Display Persian date for created_at"""
        from ..utils import get_persian_date_display
        return get_persian_date_display(obj.created_at)
    created_at_display.short_description = 'تاریخ ایجاد'


class AnalyticsActionMixin:
    """Mixin for analytics and reporting actions"""
    
    def export_user_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} users")
    export_user_data.short_description = 'Export user data'

    def calculate_profit_summary(self, request, queryset):
        total_balance = sum(float(a.balance) for a in queryset)
        avg_rate = sum(float(a.monthly_profit_rate) for a in queryset) / queryset.count() if queryset.count() > 0 else 0
        self.message_user(request, f"Total balance: {total_balance:,.2f}, Average rate: {avg_rate:.2f}%")
    calculate_profit_summary.short_description = 'Calculate profit summary'

    def export_account_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} accounts")
    export_account_data.short_description = 'Export account data'

    def calculate_deposit_summary(self, request, queryset):
        total_amount = sum(float(d.amount) for d in queryset)
        avg_rate = sum(float(d.monthly_profit_rate) for d in queryset) / queryset.count() if queryset.count() > 0 else 0
        self.message_user(request, f"Total deposits: {total_amount:,.2f}, Average rate: {avg_rate:.2f}%")
    calculate_deposit_summary.short_description = 'Calculate deposit summary'

    def export_deposit_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} deposits")
    export_deposit_data.short_description = 'Export deposit data'

    def calculate_transaction_summary(self, request, queryset):
        total_amount = sum(float(t.amount) for t in queryset)
        applied_count = queryset.filter(applied=True).count()
        pending_count = queryset.filter(applied=False).count()
        self.message_user(request, f"Total amount: {total_amount:,.2f}, Applied: {applied_count}, Pending: {pending_count}")
    calculate_transaction_summary.short_description = 'Calculate transaction summary'

    def export_transaction_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} transactions")
    export_transaction_data.short_description = 'Export transaction data'

    def calculate_balance_trend(self, request, queryset):
        self.message_user(request, f"Calculating balance trend for {queryset.count()} records")
    calculate_balance_trend.short_description = 'Calculate balance trend'

    def export_balance_data(self, request, queryset):
        self.message_user(request, f"Exporting data for {queryset.count()} balance records")
    export_balance_data.short_description = 'Export balance data'

    def view_transaction_summary(self, request, queryset):
        total_amount = sum(float(t.amount) for t in queryset)
        applied_count = queryset.filter(applied=True).count()
        self.message_user(request, f"Total amount: {total_amount:,.2f}, Applied: {applied_count}/{queryset.count()}")
    view_transaction_summary.short_description = 'View transaction summary'


