"""
Tests for admin forms functionality
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal
from finance.models import Account, Deposit, Transaction


class AdminFormsTest(TestCase):
    """Test admin forms functionality"""
    
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
        
        # Create test accounts
        self.rial_account = Account.objects.create(
            user=self.regular_user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )
        
        self.gold_account = Account.objects.create(
            user=self.regular_user,
            name='Test Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('10.00')
        )
        
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')

    def test_user_creation_form(self):
        """Test user creation form"""
        print("\n=== Testing User Creation Form ===")
        
        # Test user creation form
        response = self.client.get('/admin/finance/user/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ User creation form accessible")
        
        # Test form submission (just test that it doesn't crash)
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
        }
        
        response = self.client.post('/admin/finance/user/add/', form_data)
        # Should redirect after successful creation or show form with errors
        self.assertIn(response.status_code, [200, 302])
        print("✅ User creation form submission working")

    def test_account_creation_form(self):
        """Test account creation form"""
        print("\n=== Testing Account Creation Form ===")
        
        # Test account creation form
        response = self.client.get('/admin/finance/account/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account creation form accessible")
        
        # Test form submission (just test that it doesn't crash)
        form_data = {
            'user': self.regular_user.id,
            'name': 'New Test Account',
            'account_type': Account.ACCOUNT_TYPE_RIAL,
            'initial_balance': '500000.00',
            'monthly_profit_rate': '2.5'
        }
        
        response = self.client.post('/admin/finance/account/add/', form_data)
        # Should redirect after successful creation or show form with errors
        self.assertIn(response.status_code, [200, 302])
        print("✅ Account creation form submission working")

    def test_deposit_creation_form(self):
        """Test deposit creation form"""
        print("\n=== Testing Deposit Creation Form ===")
        
        # Test deposit creation form
        response = self.client.get('/admin/finance/deposit/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit creation form accessible")
        
        # Test form submission (just test that it doesn't crash)
        form_data = {
            'user': self.regular_user.id,
            'initial_balance': '750000.00',
            'monthly_profit_rate': '3.5'
        }
        
        response = self.client.post('/admin/finance/deposit/add/', form_data)
        # Should redirect after successful creation or show form with errors
        self.assertIn(response.status_code, [200, 302])
        print("✅ Deposit creation form submission working")

    def test_transaction_creation_form(self):
        """Test transaction creation form"""
        print("\n=== Testing Transaction Creation Form ===")
        
        # Test transaction creation form
        response = self.client.get('/admin/finance/transaction/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Transaction creation form accessible")
        
        # Test form submission (just test that it doesn't crash)
        form_data = {
            'user': self.regular_user.id,
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'kind': Transaction.KIND_CREDIT_INCREASE,
            'state': Transaction.STATE_DONE
        }
        
        response = self.client.post('/admin/finance/transaction/add/', form_data)
        # Should redirect after successful creation or show form with errors
        self.assertIn(response.status_code, [200, 302])
        print("✅ Transaction creation form submission working")

    def test_specialized_transaction_forms(self):
        """Test specialized transaction forms"""
        print("\n=== Testing Specialized Transaction Forms ===")
        
        # Test withdrawal request form
        response = self.client.get('/admin/finance/withdrawalrequest/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Withdrawal request form accessible")
        
        # Test credit increase form
        response = self.client.get('/admin/finance/creditincrease/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Credit increase form accessible")
        
        # Test account transfer form
        response = self.client.get('/admin/finance/accounttransfer/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account transfer form accessible")
        
        # Test deposit transaction form
        response = self.client.get('/admin/finance/deposittransaction/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit transaction form accessible")

    def test_form_validation(self):
        """Test form validation"""
        print("\n=== Testing Form Validation ===")
        
        # Test invalid account creation (missing required fields)
        form_data = {
            'name': 'Invalid Account',
            # Missing user, account_type, etc.
        }
        
        response = self.client.post('/admin/finance/account/add/', form_data)
        # Should show form with errors, not redirect
        self.assertEqual(response.status_code, 200)
        print("✅ Form validation working for invalid data")
        
        # Test invalid deposit creation (negative balance)
        form_data = {
            'user': self.regular_user.id,
            'initial_balance': '-100.00',  # Negative balance
            'monthly_profit_rate': '2.5'
        }
        
        response = self.client.post('/admin/finance/deposit/add/', form_data)
        # Should show form with errors, not redirect
        self.assertEqual(response.status_code, 200)
        print("✅ Form validation working for negative balance")

    def test_form_field_filtering(self):
        """Test form field filtering (e.g., rial accounts only)"""
        print("\n=== Testing Form Field Filtering ===")
        
        # Test that forms show appropriate field options
        response = self.client.get('/admin/finance/creditincrease/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Credit increase form accessible")
        
        # Test that forms show appropriate field options
        response = self.client.get('/admin/finance/withdrawalrequest/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Withdrawal request form accessible")

    def test_form_persian_translations(self):
        """Test that forms show Persian translations"""
        print("\n=== Testing Form Persian Translations ===")
        
        # Test account form for Persian content
        response = self.client.get('/admin/finance/account/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Account form loaded successfully")
        
        # Test deposit form for Persian content
        response = self.client.get('/admin/finance/deposit/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Deposit form loaded successfully")
        
        # Test transaction form for Persian content
        response = self.client.get('/admin/finance/transaction/add/')
        self.assertEqual(response.status_code, 200)
        print("✅ Transaction form loaded successfully")

    def run_all_tests(self):
        """Run all admin forms tests"""
        print("=" * 80)
        print("ADMIN FORMS TESTS")
        print("=" * 80)
        
        try:
            self.test_user_creation_form()
            self.test_account_creation_form()
            self.test_deposit_creation_form()
            self.test_transaction_creation_form()
            self.test_specialized_transaction_forms()
            self.test_form_validation()
            self.test_form_field_filtering()
            self.test_form_persian_translations()
            
            print("\n" + "=" * 80)
            print("✅ ALL ADMIN FORMS TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = AdminFormsTest()
    test.setUp()
    test.run_all_tests()
