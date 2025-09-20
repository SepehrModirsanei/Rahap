"""
Tests for Account model functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from finance.models import Account, Transaction


class AccountModelTest(TestCase):
    """Test Account model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get the base account created by User model
        self.base_account = self.user.accounts.filter(name='حساب پایه').first()
        
        # Create additional test accounts
        self.rial_account = Account.objects.create(
            user=self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('2.5')
        )
        
        self.gold_account = Account.objects.create(
            user=self.user,
            name='Test Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('20.00'),
            monthly_profit_rate=Decimal('1.5')
        )

    def test_account_creation(self):
        """Test account creation and properties"""
        print("\n=== Testing Account Creation ===")
        
        # Test rial account
        print(f"Rial account: {self.rial_account.name}")
        print(f"Type: {self.rial_account.account_type}")
        print(f"Balance: {self.rial_account.balance}")
        print(f"Profit rate: {self.rial_account.monthly_profit_rate}%")
        
        self.assertEqual(self.rial_account.account_type, Account.ACCOUNT_TYPE_RIAL)
        self.assertEqual(self.rial_account.initial_balance, Decimal('1000000.00'))
        self.assertEqual(self.rial_account.monthly_profit_rate, Decimal('2.5'))
        
        # Test gold account
        print(f"Gold account: {self.gold_account.name}")
        print(f"Type: {self.gold_account.account_type}")
        print(f"Balance: {self.gold_account.balance}")
        print(f"Profit rate: {self.gold_account.monthly_profit_rate}%")
        
        self.assertEqual(self.gold_account.account_type, Account.ACCOUNT_TYPE_GOLD)
        self.assertEqual(self.gold_account.initial_balance, Decimal('20.00'))
        self.assertEqual(self.gold_account.monthly_profit_rate, Decimal('1.5'))
        
        print("✅ Account creation working correctly!")

    def test_account_balance_calculation(self):
        """Test account balance calculation"""
        print("\n=== Testing Account Balance Calculation ===")
        
        # Test initial balance
        initial_balance = self.rial_account.balance
        print(f"Initial balance: {initial_balance}")
        self.assertEqual(initial_balance, Decimal('1000000.00'))
        
        # Create a credit increase transaction
        credit_transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        credit_transaction.apply()
        
        # Check balance after transaction
        final_balance = self.rial_account.balance
        print(f"Balance after credit: {final_balance}")
        expected_balance = Decimal('1000000.00') + Decimal('100000.00')
        self.assertEqual(final_balance, expected_balance)
        
        print("✅ Account balance calculation working correctly!")

    def test_account_profit_calculation(self):
        """Test account profit calculation"""
        print("\n=== Testing Account Profit Calculation ===")
        
        # Test profit calculation
        initial_balance = self.rial_account.balance
        print(f"Initial balance: {initial_balance}")
        
        # Calculate profit
        self.rial_account.accrue_monthly_profit()
        
        final_balance = self.rial_account.balance
        print(f"Balance after profit: {final_balance}")
        
        # Profit should be calculated based on initial balance
        expected_profit = (self.rial_account.initial_balance * self.rial_account.monthly_profit_rate) / 100
        expected_balance = initial_balance + expected_profit
        print(f"Expected profit: {expected_profit}")
        print(f"Expected balance: {expected_balance}")
        
        self.assertEqual(final_balance, expected_balance)
        
        print("✅ Account profit calculation working correctly!")

    def test_account_types(self):
        """Test different account types"""
        print("\n=== Testing Account Types ===")
        
        # Test rial account
        self.assertEqual(self.rial_account.account_type, Account.ACCOUNT_TYPE_RIAL)
        print(f"Rial account type: {self.rial_account.account_type}")
        
        # Test gold account
        self.assertEqual(self.gold_account.account_type, Account.ACCOUNT_TYPE_GOLD)
        print(f"Gold account type: {self.gold_account.account_type}")
        
        # Test foreign currency account
        foreign_account = Account.objects.create(
            user=self.user,
            name='Test Foreign Account',
            account_type=Account.ACCOUNT_TYPE_FOREIGN,
            initial_balance=Decimal('1000.00'),
            monthly_profit_rate=Decimal('1.0')
        )
        
        self.assertEqual(foreign_account.account_type, Account.ACCOUNT_TYPE_FOREIGN)
        print(f"Foreign account type: {foreign_account.account_type}")
        
        print("✅ Account types working correctly!")

    def test_account_validation(self):
        """Test account validation"""
        print("\n=== Testing Account Validation ===")
        
        # Test valid account creation
        valid_account = Account.objects.create(
            user=self.user,
            name='Valid Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('500000.00'),
            monthly_profit_rate=Decimal('2.0')
        )
        
        self.assertIsNotNone(valid_account)
        print(f"Valid account created: {valid_account.name}")
        
        # Test account clean method
        try:
            valid_account.clean()
            print("✅ Account validation passed")
        except Exception as e:
            self.fail(f"Account validation failed: {e}")
        
        print("✅ Account validation working correctly!")

    def test_account_string_representation(self):
        """Test account string representation"""
        print("\n=== Testing Account String Representation ===")
        
        # Test string representation
        account_str = str(self.rial_account)
        print(f"Account string: {account_str}")
        
        expected_str = f"Account({self.user.username}:{self.rial_account.name}:{self.rial_account.account_type})"
        self.assertEqual(account_str, expected_str)
        
        print("✅ Account string representation working correctly!")

    def run_all_tests(self):
        """Run all account model tests"""
        print("=" * 80)
        print("ACCOUNT MODEL TESTS")
        print("=" * 80)
        
        try:
            self.test_account_creation()
            self.test_account_balance_calculation()
            self.test_account_profit_calculation()
            self.test_account_types()
            self.test_account_validation()
            self.test_account_string_representation()
            
            print("\n" + "=" * 80)
            print("✅ ALL ACCOUNT MODEL TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = AccountModelTest()
    test.setUp()
    test.run_all_tests()
