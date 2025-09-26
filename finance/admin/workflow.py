"""
Admin Workflow System

This module implements a proper workflow system for credit increase and withdrawal requests
that flow between different admin types with appropriate permissions and actions.

WORKFLOW DEFINITIONS:

CREDIT INCREASE WORKFLOW:
1. Created by User/Operation Admin → STATE_WAITING_TREASURY
2. Treasury Admin → STATE_WAITING_SANDOGH  
3. Treasury Admin (Sandogh function) → STATE_APPROVED_BY_SANDOGH
4. Operation Admin → STATE_DONE

WITHDRAWAL REQUEST WORKFLOW:
1. Created by User/Operation Admin → STATE_WAITING_FINANCE_MANAGER
2. Finance Manager → STATE_APPROVED_BY_FINANCE_MANAGER
3. Treasury Admin → STATE_WAITING_SANDOGH
4. Treasury Admin (Sandogh function) → STATE_APPROVED_BY_SANDOGH (with receipt upload)
5. Operation Admin → STATE_DONE
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import transaction
from ..models import Transaction, TransactionStateLog
from .mixins import ReadOnlyMixin, TreasuryMixin, OperationMixin


class WorkflowMixin:
    """Mixin for workflow-related functionality"""
    
    def get_workflow_status_display(self, obj):
        """Display workflow status with color coding"""
        status_colors = {
            Transaction.STATE_WAITING_TREASURY: 'orange',
            Transaction.STATE_WAITING_SANDOGH: 'blue', 
            Transaction.STATE_VERIFIED_KHAZANEDAR: 'purple',
            Transaction.STATE_WAITING_FINANCE_MANAGER: 'brown',
            Transaction.STATE_APPROVED_BY_FINANCE_MANAGER: 'darkgreen',
            Transaction.STATE_APPROVED_BY_SANDOGH: 'green',
            Transaction.STATE_DONE: 'green',
            Transaction.STATE_REJECTED: 'red'
        }
        
        color = status_colors.get(obj.state, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_state_display()
        )
    get_workflow_status_display.short_description = 'وضعیت'
    
    def get_workflow_progress(self, obj):
        """Display workflow progress bar"""
        # Define workflow steps for each transaction type
        if obj.kind == Transaction.KIND_CREDIT_INCREASE:
            progress_steps = [
                (Transaction.STATE_WAITING_TREASURY, 'خزانه‌داری'),
                (Transaction.STATE_WAITING_SANDOGH, 'صندوق'),
                (Transaction.STATE_APPROVED_BY_SANDOGH, 'تایید صندوق'),
                (Transaction.STATE_DONE, 'انجام شده')
            ]
        elif obj.kind == Transaction.KIND_WITHDRAWAL_REQUEST:
            progress_steps = [
                (Transaction.STATE_WAITING_FINANCE_MANAGER, 'مدیر مالی'),
                (Transaction.STATE_APPROVED_BY_FINANCE_MANAGER, 'تایید مدیر مالی'),
                (Transaction.STATE_WAITING_SANDOGH, 'صندوق'),
                (Transaction.STATE_APPROVED_BY_SANDOGH, 'تایید صندوق'),
                (Transaction.STATE_DONE, 'انجام شده')
            ]
        else:
            progress_steps = [
                (Transaction.STATE_WAITING_TREASURY, 'خزانه‌داری'),
                (Transaction.STATE_DONE, 'انجام شده')
            ]
        
        current_step = 0
        for i, (state, label) in enumerate(progress_steps):
            if obj.state == state:
                current_step = i + 1
                break
        
        progress_html = '<div style="width: 100%; background-color: #f0f0f0; border-radius: 5px;">'
        progress_html += f'<div style="width: {(current_step / len(progress_steps)) * 100}%; background-color: #4CAF50; height: 20px; border-radius: 5px; text-align: center; color: white; line-height: 20px;">'
        progress_html += f'{current_step}/{len(progress_steps)}</div></div>'
        
        return format_html(progress_html)
    get_workflow_progress.short_description = 'پیشرفت'
    
    def get_next_action_display(self, obj):
        """Display what the next action should be"""
        next_actions = {
            Transaction.STATE_WAITING_TREASURY: 'بررسی توسط خزانه‌داری',
            Transaction.STATE_WAITING_SANDOGH: 'تایید توسط صندوق',
            Transaction.STATE_VERIFIED_KHAZANEDAR: 'انجام تراکنش',
            Transaction.STATE_WAITING_FINANCE_MANAGER: 'تایید مدیر مالی',
            Transaction.STATE_APPROVED_BY_FINANCE_MANAGER: 'بررسی توسط خزانه‌داری',
            Transaction.STATE_APPROVED_BY_SANDOGH: 'انجام تراکنش توسط عملیات',
            Transaction.STATE_DONE: 'انجام شده',
            Transaction.STATE_REJECTED: 'رد شده'
        }
        
        return next_actions.get(obj.state, 'نامشخص')
    get_next_action_display.short_description = 'اقدام بعدی'

    def get_source_account_display(self, obj):
        """Display source account with name and type"""
        try:
            if obj.source_account:
                return f"{obj.source_account.name} ({obj.source_account.get_account_type_display()})"
            return "-"
        except Exception:
            return "-"
    get_source_account_display.short_description = 'حساب مبدا'
    get_source_account_display.admin_order_field = 'source_account'

    def get_destination_account_display(self, obj):
        """Display destination account with name and type"""
        try:
            if obj.destination_account:
                return f"{obj.destination_account.name} ({obj.destination_account.get_account_type_display()})"
            return "-"
        except Exception:
            return "-"
    get_destination_account_display.short_description = 'حساب مقصد'
    get_destination_account_display.admin_order_field = 'destination_account'

    def get_list_display(self, request):
        """Get list display with workflow columns"""
        return [
            'transaction_code', 'user', 'kind', 'amount', 
            'get_source_account_display', 'get_destination_account_display',
            'get_workflow_status_display', 'get_workflow_progress',
            'get_next_action_display', 'created_at'
        ]


class TreasuryWorkflowMixin(TreasuryMixin, WorkflowMixin):
    """Treasury admin workflow mixin - handles both treasury and sandogh functions"""
    
    def get_queryset(self, request):
        """Filter transactions for treasury admin"""
        from django.contrib import admin
        qs = admin.ModelAdmin.get_queryset(self, request)
        # Treasury admin sees transactions waiting for treasury approval AND sandogh processing
        return qs.filter(state__in=[
            Transaction.STATE_WAITING_TREASURY,
            Transaction.STATE_APPROVED_BY_FINANCE_MANAGER,
            Transaction.STATE_WAITING_SANDOGH
        ])
    
    actions = ['approve_for_sandogh', 'verify_sandogh', 'reject_transaction']
    
    def approve_for_sandogh(self, request, queryset):
        """Approve transactions for sandogh processing"""
        moved = 0
        for txn in queryset:
            if txn.state in [Transaction.STATE_WAITING_TREASURY, Transaction.STATE_APPROVED_BY_FINANCE_MANAGER]:
                txn.state = Transaction.STATE_WAITING_SANDOGH
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Approved {moved} transaction(s) for sandogh processing")
    approve_for_sandogh.short_description = 'تایید برای صندوق'
    
    def verify_sandogh(self, request, queryset):
        """Verify transactions as sandogh (Treasury Admin's sandogh function)"""
        moved = 0
        for txn in queryset:
            if txn.state == Transaction.STATE_WAITING_SANDOGH:
                txn.state = Transaction.STATE_APPROVED_BY_SANDOGH
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Verified {moved} transaction(s) as sandogh")
    verify_sandogh.short_description = 'تایید صندوق'
    
    def reject_transaction(self, request, queryset):
        """Reject transactions"""
        moved = 0
        for txn in queryset:
            if txn.state not in [Transaction.STATE_DONE, Transaction.STATE_REJECTED]:
                txn.state = Transaction.STATE_REJECTED
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Rejected {moved} transaction(s)")
    reject_transaction.short_description = 'رد تراکنش'


# Sandogh functionality is now part of Treasury Admin


class FinanceManagerWorkflowMixin(WorkflowMixin):
    """Finance manager workflow mixin"""
    
    def get_queryset(self, request):
        """Filter transactions for finance manager"""
        from django.contrib import admin
        qs = admin.ModelAdmin.get_queryset(self, request)
        # Finance manager sees withdrawal requests waiting for approval
        return qs.filter(
            state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            kind=Transaction.KIND_WITHDRAWAL_REQUEST
        )
    
    actions = ['approve_finance_manager', 'reject_transaction']
    
    def approve_finance_manager(self, request, queryset):
        """Approve transactions as finance manager"""
        moved = 0
        for txn in queryset:
            if txn.state == Transaction.STATE_WAITING_FINANCE_MANAGER:
                txn.state = Transaction.STATE_APPROVED_BY_FINANCE_MANAGER
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Approved {moved} transaction(s) as finance manager")
    approve_finance_manager.short_description = 'تایید مدیر مالی'
    
    def reject_transaction(self, request, queryset):
        """Reject transactions"""
        moved = 0
        for txn in queryset:
            if txn.state == Transaction.STATE_WAITING_FINANCE_MANAGER:
                txn.state = Transaction.STATE_REJECTED
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Rejected {moved} transaction(s)")
    reject_transaction.short_description = 'رد تراکنش'


class OperationWorkflowMixin(OperationMixin, WorkflowMixin):
    """Operation admin workflow mixin"""
    
    def get_queryset(self, request):
        """Filter transactions for operation admin"""
        from django.contrib import admin
        qs = admin.ModelAdmin.get_queryset(self, request)
        # Operation admin sees transactions approved by sandogh
        return qs.filter(state=Transaction.STATE_APPROVED_BY_SANDOGH)
    
    actions = ['complete_transaction', 'reject_transaction']
    
    def complete_transaction(self, request, queryset):
        """Complete transactions"""
        moved = 0
        for txn in queryset:
            if txn.state == Transaction.STATE_APPROVED_BY_SANDOGH:
                # Enforce receipt for withdrawal requests when moving to DONE (step 4 -> 5)
                if txn.kind == Transaction.KIND_WITHDRAWAL_REQUEST and not txn.receipt:
                    self.message_user(request, f"رسید برای اتمام درخواست برداشت {txn.transaction_code} الزامی است.", level=messages.ERROR)
                    continue
                txn.state = Transaction.STATE_DONE
                txn._changed_by = request.user
                txn.save()
                # Auto-apply the transaction
                txn.apply()
                moved += 1
        self.message_user(request, f"Completed {moved} transaction(s)")
    complete_transaction.short_description = 'انجام تراکنش'
    
    def reject_transaction(self, request, queryset):
        """Reject transactions"""
        moved = 0
        for txn in queryset:
            if txn.state == Transaction.STATE_APPROVED_BY_SANDOGH:
                txn.state = Transaction.STATE_REJECTED
                txn._changed_by = request.user
                txn.save()
                moved += 1
        self.message_user(request, f"Rejected {moved} transaction(s)")
    reject_transaction.short_description = 'رد تراکنش'


class SupervisorWorkflowMixin(ReadOnlyMixin, WorkflowMixin):
    """Supervisor admin workflow mixin (read-only oversight)"""
    
    def get_queryset(self, request):
        """Filter transactions for supervisor admin"""
        from django.contrib import admin
        qs = admin.ModelAdmin.get_queryset(self, request)
        # Supervisor sees all transactions for oversight
        return qs
    


# Workflow-specific admin classes
class TreasuryWorkflowTransactionAdmin(TreasuryWorkflowMixin, admin.ModelAdmin):
    """Treasury admin for workflow transactions"""
    list_filter = ['state', 'kind', 'created_at']
    search_fields = ['transaction_code', 'user__username']
    readonly_fields = ['transaction_code', 'created_at', 'applied']
    
    fieldsets = (
        ('اطلاعات تراکنش', {
            'fields': ('transaction_code', 'user', 'kind', 'amount', 'state')
        }),
        ('اطلاعات برداشت', {
            'fields': ('withdrawal_card_number', 'withdrawal_sheba_number')
        }),
        ('نظرات همه کارکنان', {
            'fields': ('user_comment', 'finance_manager_opinion', 'treasurer_opinion', 'admin_opinion'),
            'description': 'نظرات کاربر، مدیر مالی، خزانه‌دار و ادمین عملیات'
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'applied'),
            'classes': ('collapse',)
        }),
    )


class FinanceManagerWorkflowTransactionAdmin(FinanceManagerWorkflowMixin, admin.ModelAdmin):
    """Finance manager admin for withdrawal requests"""
    list_filter = ['state', 'kind', 'created_at']
    search_fields = ['transaction_code', 'user__username']
    readonly_fields = ['transaction_code', 'created_at', 'applied']
    
    fieldsets = (
        ('اطلاعات تراکنش', {
            'fields': ('transaction_code', 'user', 'kind', 'amount', 'state')
        }),
        ('اطلاعات برداشت', {
            'fields': ('withdrawal_card_number', 'withdrawal_sheba_number')
        }),
        ('نظرات همه کارکنان', {
            'fields': ('user_comment', 'finance_manager_opinion', 'treasurer_opinion', 'admin_opinion'),
            'description': 'نظرات کاربر، مدیر مالی، خزانه‌دار و ادمین عملیات'
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'applied'),
            'classes': ('collapse',)
        }),
    )


class OperationWorkflowTransactionAdmin(OperationWorkflowMixin, admin.ModelAdmin):
    """Operation admin for completing transactions"""
    list_filter = ['state', 'kind', 'created_at']
    search_fields = ['transaction_code', 'user__username']
    readonly_fields = ['transaction_code', 'created_at', 'applied']
    
    fieldsets = (
        ('اطلاعات تراکنش', {
            'fields': ('transaction_code', 'user', 'kind', 'amount', 'state')
        }),
        ('اطلاعات برداشت', {
            'fields': ('withdrawal_card_number', 'withdrawal_sheba_number')
        }),
        ('نظرات همه کارکنان', {
            'fields': ('user_comment', 'finance_manager_opinion', 'treasurer_opinion', 'admin_opinion'),
            'description': 'نظرات کاربر، مدیر مالی، خزانه‌دار و ادمین عملیات'
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'applied'),
            'classes': ('collapse',)
        }),
    )


class SupervisorWorkflowTransactionAdmin(SupervisorWorkflowMixin, admin.ModelAdmin):
    """Supervisor admin for workflow oversight"""
    list_filter = ['state', 'kind', 'created_at']
    search_fields = ['transaction_code', 'user__username']
    readonly_fields = ['transaction_code', 'created_at', 'applied']
    
    fieldsets = (
        ('اطلاعات تراکنش', {
            'fields': ('transaction_code', 'user', 'kind', 'amount', 'state')
        }),
        ('اطلاعات برداشت', {
            'fields': ('withdrawal_card_number', 'withdrawal_sheba_number')
        }),
        ('نظرات همه کارکنان', {
            'fields': ('user_comment', 'finance_manager_opinion', 'treasurer_opinion', 'admin_opinion'),
            'description': 'نظرات کاربر، مدیر مالی، خزانه‌دار و ادمین عملیات'
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'applied'),
            'classes': ('collapse',)
        }),
    )
