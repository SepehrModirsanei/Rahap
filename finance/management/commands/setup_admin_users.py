"""
Management command to set up admin users and permissions for different admin sites
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from finance.models import User, Account, Deposit, Transaction


class Command(BaseCommand):
    help = 'Set up admin users and permissions for different admin sites'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all admin users and permissions',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.reset_admin_users()
        
        self.create_groups()
        self.create_admin_users()
        self.setup_permissions()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up admin users and permissions!')
        )

    def reset_admin_users(self):
        """Reset admin users and groups"""
        # Delete existing admin users
        admin_usernames = [
            'treasury_admin', 'finance_manager', 'operation_admin', 
            'supervisor_admin', 'analytics_admin'
        ]
        
        for username in admin_usernames:
            try:
                user = User.objects.get(username=username)
                user.delete()
                self.stdout.write(f'Deleted user: {username}')
            except User.DoesNotExist:
                pass
        
        # Delete existing groups
        group_names = [
            'Treasury Admin', 'Finance Manager', 'Operation Admin',
            'Supervisor', 'Analytics Admin'
        ]
        
        for group_name in group_names:
            try:
                group = Group.objects.get(name=group_name)
                group.delete()
                self.stdout.write(f'Deleted group: {group_name}')
            except Group.DoesNotExist:
                pass

    def create_groups(self):
        """Create groups for different admin roles"""
        groups_data = [
            ('Treasury Admin', 'مدیر خزانه‌داری'),
            ('Finance Manager', 'مدیر مالی'),
            ('Operation Admin', 'مدیر عملیات'),
            ('Supervisor', 'مدیر نظارت'),
            ('Analytics Admin', 'مدیر تحلیل‌ها')
        ]
        
        for group_name, verbose_name in groups_data:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')
            else:
                self.stdout.write(f'Group {group_name} already exists')

    def create_admin_users(self):
        """Create admin users for different roles"""
        admin_users = [
            ('treasury_admin', 'treasury@example.com', 'Treasury Admin', 'خزانه‌دار'),
            ('finance_manager', 'finance@example.com', 'Finance Manager', 'مدیر مالی'),
            ('operation_admin', 'operation@example.com', 'Operation Admin', 'مدیر عملیات'),
            ('supervisor_admin', 'supervisor@example.com', 'Supervisor', 'مدیر نظارت'),
            ('analytics_admin', 'analytics@example.com', 'Analytics Admin', 'مدیر تحلیل‌ها')
        ]
        
        for username, email, group_name, display_name in admin_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_active': True,
                    'first_name': display_name
                }
            )
            
            if created:
                user.set_password('admin123')  # Default password
                user.save()
                
                # Add user to appropriate group
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created admin user: {username} (password: admin123)')
                )
            else:
                self.stdout.write(f'Admin user {username} already exists')

    def setup_permissions(self):
        """Set up permissions for different admin roles"""
        # Get content types
        try:
            user_ct = ContentType.objects.get_for_model(User)
            account_ct = ContentType.objects.get_for_model(Account)
            deposit_ct = ContentType.objects.get_for_model(Deposit)
            transaction_ct = ContentType.objects.get_for_model(Transaction)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting content types: {e}')
            )
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
                ('view_user', 'Can view user'),
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
                        self.stdout.write(f'Added permission {perm_codename} to {group_name}')
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Permission {perm_codename} not found')
                        )
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Group {group_name} not found')
                )

    def print_admin_info(self):
        """Print information about created admin users"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('ADMIN USERS CREATED:')
        self.stdout.write('='*50)
        
        admin_info = [
            ('treasury_admin', 'Treasury Admin', '/admin/treasury/'),
            ('finance_manager', 'Finance Manager', '/admin/finance-manager/'),
            ('operation_admin', 'Operation Admin', '/admin/operations/'),
            ('supervisor_admin', 'Supervisor', '/admin/supervisor/'),
            ('analytics_admin', 'Analytics Admin', '/admin/analytics/'),
        ]
        
        for username, role, url in admin_info:
            self.stdout.write(f'{role}: {username} (password: admin123)')
            self.stdout.write(f'  URL: http://127.0.0.1:8000{url}')
            self.stdout.write('')
        
        self.stdout.write('MAIN ADMIN (Full Access):')
        self.stdout.write('  URL: http://127.0.0.1:8000/admin/')
        self.stdout.write('  Use your superuser account')
        self.stdout.write('')
        
        self.stdout.write(
            self.style.WARNING(
                'IMPORTANT: Change default passwords (admin123) in production!'
            )
        )
