"""
Custom Authentication for Admin Sites

This module provides different authentication methods for different admin sites,
allowing role-based access control for different admin types.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.admin import AdminSite
from django.contrib.auth.backends import ModelBackend


class RoleBasedAdminSite(AdminSite):
    """
    Base class for role-based admin sites with custom authentication
    """
    
    def __init__(self, name='admin', required_role=None):
        super().__init__(name)
        self.required_role = required_role
    
    def has_permission(self, request):
        """
        Check if user has permission to access this admin site
        """
        if not request.user.is_authenticated:
            return False
        
        # Superuser has access to all sites
        if request.user.is_superuser:
            return True
        
        # Check if user has the required role
        if self.required_role:
            return self._user_has_role(request.user, self.required_role)
        
        return True
    
    def _user_has_role(self, user, required_role):
        """
        Check if user has the required role
        """
        # Check user profile for role (if you have a UserProfile model)
        if hasattr(user, 'profile') and hasattr(user.profile, 'role'):
            return user.profile.role == required_role
        
        # Check user groups for role
        if hasattr(user, 'groups'):
            role_groups = {
                'treasury': 'Treasury Admin',
                'finance_manager': 'Finance Manager',
                'operation': 'Operation Admin',
                'supervisor': 'Supervisor',
                'analytics': 'Analytics Admin'
            }
            group_name = role_groups.get(required_role)
            if group_name:
                return user.groups.filter(name=group_name).exists()
        
        # Check user permissions
        role_permissions = {
            'treasury': 'finance.can_manage_treasury',
            'finance_manager': 'finance.can_manage_finance',
            'operation': 'finance.can_manage_operations',
            'supervisor': 'finance.can_supervise',
            'analytics': 'finance.can_view_analytics'
        }
        
        permission = role_permissions.get(required_role)
        if permission:
            return user.has_perm(permission)
        
        return False
    
    def login(self, request, extra_context=None):
        """
        Custom login view with role checking
        """
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            if username and password:
                user = authenticate(request, username=username, password=password)
                if user and self.has_permission(request):
                    from django.contrib.auth import login
                    login(request, user)
                    return super().login(request, extra_context)
                else:
                    # Add error message for invalid role
                    from django.contrib import messages
                    messages.error(request, f'شما دسترسی به {self.site_header} ندارید.')
        
        return super().login(request, extra_context)


class TreasuryAdminSite(RoleBasedAdminSite):
    """Treasury Admin Site with treasury role requirement"""
    
    def __init__(self, name='treasury_admin'):
        super().__init__(name, required_role='treasury')
        self.site_header = "مدیریت خزانه‌داری"
        self.site_title = "مدیریت خزانه‌داری"
        self.index_title = "مدیریت خزانه‌داری"


class FinanceManagerAdminSite(RoleBasedAdminSite):
    """Finance Manager Admin Site with finance_manager role requirement"""
    
    def __init__(self, name='finance_manager_admin'):
        super().__init__(name, required_role='finance_manager')
        self.site_header = "مدیریت مالی"
        self.site_title = "مدیریت مالی"
        self.index_title = "مدیریت کامل مالی"
        self.site_url = "/admin/finance-manager/"


class OperationAdminSite(RoleBasedAdminSite):
    """Operation Admin Site with operation role requirement"""
    
    def __init__(self, name='operation_admin'):
        super().__init__(name, required_role='operation')
        self.site_header = "مدیریت عملیات"
        self.site_title = "مدیریت عملیات"
        self.index_title = "مدیریت عملیات روزانه"
        self.site_url = "/admin/operations/"


class SupervisorAdminSite(RoleBasedAdminSite):
    """Supervisor Admin Site with supervisor role requirement"""
    
    def __init__(self, name='supervisor_admin'):
        super().__init__(name, required_role='supervisor')
        self.site_header = "مدیریت نظارت"
        self.site_title = "مدیریت نظارت"
        self.index_title = "مدیریت نظارت مالی"
        self.site_url = "/admin/supervisor/"


class AnalyticsAdminSite(RoleBasedAdminSite):
    """Analytics Admin Site with analytics role requirement"""
    
    def __init__(self, name='analytics_admin'):
        super().__init__(name, required_role='analytics')
        self.site_header = "مدیریت تحلیل‌ها"
        self.site_title = "مدیریت تحلیل‌ها"
        self.index_title = "مدیریت تحلیل‌های مالی"
        self.site_url = "/admin/analytics/"


def create_admin_users():
    """
    Create admin users for different roles
    This function should be called during setup
    """
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Create groups for different admin roles
    groups_data = [
        ('Treasury Admin', 'treasury_admin', 'مدیر خزانه‌داری'),
        ('Finance Manager', 'finance_manager_admin', 'مدیر مالی'),
        ('Operation Admin', 'operation_admin', 'مدیر عملیات'),
        ('Supervisor', 'supervisor_admin', 'مدیر نظارت'),
        ('Analytics Admin', 'analytics_admin', 'مدیر تحلیل‌ها')
    ]
    
    for group_name, codename, verbose_name in groups_data:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"Created group: {group_name}")
    
    # Create specific admin users for each role
    admin_users = [
        ('treasury_admin', 'treasury@example.com', 'Treasury Admin'),
        ('finance_manager', 'finance@example.com', 'Finance Manager'),
        ('operation_admin', 'operation@example.com', 'Operation Admin'),
        ('supervisor_admin', 'supervisor@example.com', 'Supervisor'),
        ('analytics_admin', 'analytics@example.com', 'Analytics Admin')
    ]
    
    for username, email, group_name in admin_users:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_active': True
            }
        )
        
        if created:
            user.set_password('admin123')  # Default password - should be changed
            user.save()
            
            # Add user to appropriate group
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            
            print(f"Created admin user: {username} (password: admin123)")
        else:
            print(f"Admin user {username} already exists")


def setup_admin_permissions():
    """
    Set up permissions for different admin roles
    """
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Get content types for finance models
    try:
        user_ct = ContentType.objects.get_for_model(User)
        account_ct = ContentType.objects.get_for_model(Account)
        deposit_ct = ContentType.objects.get_for_model(Deposit)
        transaction_ct = ContentType.objects.get_for_model(Transaction)
    except:
        print("Models not found. Make sure to run migrations first.")
        return
    
    # Define permissions for each role
    role_permissions = {
        'Treasury Admin': [
            ('add_transaction', 'Can add transaction'),
            ('change_transaction', 'Can change transaction'),
            ('view_transaction', 'Can view transaction'),
            ('add_account', 'Can add account'),
            ('change_account', 'Can change account'),
            ('view_account', 'Can view account'),
        ],
        'Finance Manager': [
            ('view_transaction', 'Can view transaction'),
            ('change_transaction', 'Can change transaction'),
            ('view_user', 'Can view user'),
            ('view_account', 'Can view account'),
        ],
        'Operation Admin': [
            ('add_transaction', 'Can add transaction'),
            ('change_transaction', 'Can change transaction'),
            ('view_transaction', 'Can view transaction'),
            ('view_user', 'Can view user'),
            ('view_account', 'Can view account'),
        ],
        'Supervisor': [
            ('view_transaction', 'Can view transaction'),
            ('view_user', 'Can view user'),
            ('view_account', 'Can view account'),
            ('view_deposit', 'Can view deposit'),
        ],
        'Analytics Admin': [
            ('view_transaction', 'Can view transaction'),
            ('view_user', 'Can view user'),
            ('view_account', 'Can view account'),
            ('view_deposit', 'Can view deposit'),
        ]
    }
    
    for group_name, permissions in role_permissions.items():
        try:
            group = Group.objects.get(name=group_name)
            for perm_codename, perm_name in permissions:
                # Try to find the permission
                permission = Permission.objects.filter(
                    codename=perm_codename,
                    content_type__in=[user_ct, account_ct, deposit_ct, transaction_ct]
                ).first()
                
                if permission:
                    group.permissions.add(permission)
                    print(f"Added permission {perm_codename} to {group_name}")
        except Group.DoesNotExist:
            print(f"Group {group_name} not found")
