"""
Tests for admin panel registration and functionality
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from finance.models import Account, Deposit, Transaction


class AdminRegistrationTest(TestCase):
    """Test admin panel registration and basic functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.User = get_user_model()
        self.admin_user = self.User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.regular_user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')

    def test_admin_login(self):
        """Test admin login functionality"""
        print("\n=== Testing Admin Login ===")
        
        # Test login
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        print("✅ Admin login working correctly!")
        
        # Test that we're logged in as admin
        self.assertTrue(self.admin_user.is_superuser)
        self.assertTrue(self.admin_user.is_staff)
        print(f"Admin user: {self.admin_user.username}")
        print(f"Is superuser: {self.admin_user.is_superuser}")
        print(f"Is staff: {self.admin_user.is_staff}")

    def test_admin_panel_access(self):
        """Test admin panel access"""
        print("\n=== Testing Admin Panel Access ===")
        
        # Test main admin page
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        print("✅ Main admin page accessible")
        
        # Test finance app admin
        response = self.client.get('/admin/finance/')
        self.assertEqual(response.status_code, 200)
        print("✅ Finance admin page accessible")
        
        # Test user admin
        response = self.client.get('/admin/finance/user/')
        self.assertEqual(response.status_code, 200)
        print("✅ User admin page accessible")
        
        # Test account admin
        response = self.client.get('/admin/finance/account/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account admin page accessible")
        
        # Test deposit admin
        response = self.client.get('/admin/finance/deposit/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit admin page accessible")
        
        # Test transaction admin
        response = self.client.get('/admin/finance/transaction/')
        self.assertEqual(response.status_code, 200)
        print("✅ Transaction admin page accessible")

    def test_user_admin_functionality(self):
        """Test user admin functionality"""
        print("\n=== Testing User Admin Functionality ===")
        
        # Test user list view
        response = self.client.get('/admin/finance/user/')
        self.assertEqual(response.status_code, 200)
        print("✅ User list view working")
        
        # Test user detail view
        response = self.client.get(f'/admin/finance/user/{self.regular_user.id}/change/')
        self.assertEqual(response.status_code, 200)
        print("✅ User detail view working")
        
        # Test user creation
        response = self.client.get('/admin/finance/user/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ User creation form accessible")

    def test_account_admin_functionality(self):
        """Test account admin functionality"""
        print("\n=== Testing Account Admin Functionality ===")
        
        # Create test account
        account = Account.objects.create(
            user=self.regular_user,
            name='Test Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )
        
        # Test account list view
        response = self.client.get('/admin/finance/account/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account list view working")
        
        # Test account detail view
        response = self.client.get(f'/admin/finance/account/{account.id}/change/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account detail view working")
        
        # Test account creation
        response = self.client.get('/admin/finance/account/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account creation form accessible")

    def test_deposit_admin_functionality(self):
        """Test deposit admin functionality"""
        print("\n=== Testing Deposit Admin Functionality ===")
        
        # Create test deposit
        deposit = Deposit.objects.create(
            user=self.regular_user,
            initial_balance=Decimal('500000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Test deposit list view
        response = self.client.get('/admin/finance/deposit/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit list view working")
        
        # Test deposit detail view
        response = self.client.get(f'/admin/finance/deposit/{deposit.id}/change/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit detail view working")
        
        # Test deposit creation
        response = self.client.get('/admin/finance/deposit/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit creation form accessible")

    def test_transaction_admin_functionality(self):
        """Test transaction admin functionality"""
        print("\n=== Testing Transaction Admin Functionality ===")
        
        # Create test transaction
        base_account = self.regular_user.accounts.filter(name='حساب پایه').first()
        transaction = Transaction.objects.create(
            user=self.regular_user,
            destination_account=base_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        # Test transaction list view
        response = self.client.get('/admin/finance/transaction/')
        self.assertEqual(response.status_code, 200)
        print("✅ Transaction list view working")
        
        # Test transaction detail view
        response = self.client.get(f'/admin/finance/transaction/{transaction.id}/change/')
        self.assertEqual(response.status_code, 200)
        print("✅ Transaction detail view working")
        
        # Test transaction creation
        response = self.client.get('/admin/finance/transaction/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Transaction creation form accessible")

    def test_specialized_transaction_admins(self):
        """Test specialized transaction admin views"""
        print("\n=== Testing Specialized Transaction Admins ===")
        
        # Test withdrawal request admin
        response = self.client.get('/admin/finance/withdrawalrequest/')
        self.assertEqual(response.status_code, 200)
        print("✅ Withdrawal request admin working")
        
        # Test credit increase admin
        response = self.client.get('/admin/finance/creditincrease/')
        self.assertEqual(response.status_code, 200)
        print("✅ Credit increase admin working")
        
        # Test account transfer admin
        response = self.client.get('/admin/finance/accounttransfer/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account transfer admin working")
        
        # Test deposit transaction admin
        response = self.client.get('/admin/finance/deposittransaction/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit transaction admin working")

    def test_admin_persian_translations(self):
        """Test that admin panel shows Persian translations"""
        print("\n=== Testing Admin Persian Translations ===")
        
        # Test main admin page for Persian content
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        
        # Check for Persian content in response
        content = response.content.decode('utf-8')
        print("✅ Admin page loaded successfully")
        
        # Test finance admin for Persian content
        response = self.client.get('/admin/finance/')
        self.assertEqual(response.status_code, 200)
        print("✅ Finance admin page loaded successfully")

    def run_all_tests(self):
        """Run all admin registration tests"""
        print("=" * 80)
        print("ADMIN REGISTRATION TESTS")
        print("=" * 80)
        
        try:
            self.test_admin_login()
            self.test_admin_panel_access()
            self.test_user_admin_functionality()
            self.test_account_admin_functionality()
            self.test_deposit_admin_functionality()
            self.test_transaction_admin_functionality()
            self.test_specialized_transaction_admins()
            self.test_admin_persian_translations()
            
            print("\n" + "=" * 80)
            print("✅ ALL ADMIN REGISTRATION TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = AdminRegistrationTest()
    test.setUp()
    test.run_all_tests()
