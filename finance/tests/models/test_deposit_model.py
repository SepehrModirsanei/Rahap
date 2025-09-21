"""
Tests for Deposit model functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from finance.models import Account, Deposit, Transaction


class DepositModelTest(TestCase):
    """Test Deposit model functionality"""
    
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
        
        # Create test deposits
        self.deposit1 = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        self.deposit2 = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('500000.00'),
            monthly_profit_rate=Decimal('2.5')
        )

    def test_deposit_creation(self):
        """Test deposit creation and properties"""
        print("\n=== Testing Deposit Creation ===")
        
        # Test deposit 1
        print(f"Deposit 1: {self.deposit1.initial_balance}")
        print(f"Profit rate: {self.deposit1.monthly_profit_rate}%")
        
        self.assertEqual(self.deposit1.initial_balance, Decimal('1000000.00'))
        self.assertEqual(self.deposit1.monthly_profit_rate, Decimal('3.0'))
        
        # Test deposit 2
        print(f"Deposit 2: {self.deposit2.initial_balance}")
        print(f"Profit rate: {self.deposit2.monthly_profit_rate}%")
        
        self.assertEqual(self.deposit2.initial_balance, Decimal('500000.00'))
        self.assertEqual(self.deposit2.monthly_profit_rate, Decimal('2.5'))
        
        print("✅ Deposit creation working correctly!")

    def test_deposit_balance_calculation(self):
        """Test deposit balance calculation"""
        print("\n=== Testing Deposit Balance Calculation ===")
        
        # Test initial balance
        initial_balance = self.deposit1.balance
        print(f"Initial balance: {initial_balance}")
        self.assertEqual(initial_balance, Decimal('1000000.00'))
        
        # Create a transaction to the deposit
        deposit_transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.base_account,
            destination_deposit=self.deposit1,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
            state=Transaction.STATE_DONE
        )
        deposit_transaction.apply()
        
        # Check balance after transaction
        final_balance = self.deposit1.balance
        print(f"Balance after transaction: {final_balance}")
        expected_balance = Decimal('1000000.00') + Decimal('100000.00')
        self.assertEqual(final_balance, expected_balance)
        
        print("✅ Deposit balance calculation working correctly!")

    def test_deposit_profit_calculation(self):
        """Test deposit profit calculation"""
        print("\n=== Testing Deposit Profit Calculation ===")
        
        # Test profit calculation
        initial_balance = self.deposit1.balance
        print(f"Initial balance: {initial_balance}")
        
        # Calculate profit
        self.deposit1.accrue_monthly_profit()
        
        final_balance = self.deposit1.balance
        print(f"Balance after profit: {final_balance}")
        
        # Deposit profit should go to base account, not back to deposit
        self.assertEqual(final_balance, initial_balance)
        
        # Check that profit was sent to base account
        base_account_balance = self.base_account.balance
        expected_profit = (self.deposit1.initial_balance * self.deposit1.monthly_profit_rate) / 100
        print(f"Base account balance: {base_account_balance}")
        print(f"Expected profit: {expected_profit}")
        
        self.assertEqual(base_account_balance, expected_profit)
        
        print("✅ Deposit profit calculation working correctly!")

    def test_deposit_simplified_creation(self):
        """Test simplified deposit creation without funding sources"""
        print("\n=== Testing Simplified Deposit Creation ===")
        
        # All deposits now start with zero balance
        self.assertEqual(self.deposit1.initial_balance, Decimal('1000000.00'))
        print(f"Deposit 1 initial balance: {self.deposit1.initial_balance}")
        
        # Create a new deposit with zero balance
        new_deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('0.00'),
            monthly_profit_rate=Decimal('2.0')
        )
        
        self.assertEqual(new_deposit.initial_balance, Decimal('0.00'))
        print(f"New deposit initial balance: {new_deposit.initial_balance}")
        
        print("✅ Simplified deposit creation working correctly!")

    def test_deposit_validation(self):
        """Test deposit validation"""
        print("\n=== Testing Deposit Validation ===")
        
        # Test valid deposit creation
        valid_deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('300000.00'),
            monthly_profit_rate=Decimal('2.5')
        )
        
        self.assertIsNotNone(valid_deposit)
        print(f"Valid deposit created: {valid_deposit.initial_balance}")
        
        # Test deposit clean method
        try:
            valid_deposit.clean()
            print("✅ Deposit validation passed")
        except Exception as e:
            self.fail(f"Deposit validation failed: {e}")
        
        print("✅ Deposit validation working correctly!")

    def test_deposit_string_representation(self):
        """Test deposit string representation"""
        print("\n=== Testing Deposit String Representation ===")
        
        # Test string representation
        deposit_str = str(self.deposit1)
        print(f"Deposit string: {deposit_str}")
        
        expected_str = f"Deposit({self.user.username}) initial_balance={self.deposit1.initial_balance}"
        self.assertEqual(deposit_str, expected_str)
        
        print("✅ Deposit string representation working correctly!")

    def test_deposit_profit_transaction_creation(self):
        """Test that deposit profit creates correct transaction"""
        print("\n=== Testing Deposit Profit Transaction Creation ===")
        
        # Calculate profit
        self.deposit1.accrue_monthly_profit()
        
        # Check that profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        
        self.assertEqual(profit_transactions.count(), 1)
        
        profit_transaction = profit_transactions.first()
        print(f"Profit transaction created: {profit_transaction.amount}")
        print(f"Destination: {profit_transaction.destination_account.name}")
        
        # Verify transaction properties
        expected_profit = (self.deposit1.initial_balance * self.deposit1.monthly_profit_rate) / 100
        self.assertEqual(profit_transaction.amount, expected_profit)
        self.assertEqual(profit_transaction.destination_account, self.base_account)
        self.assertEqual(profit_transaction.state, Transaction.STATE_DONE)
        self.assertTrue(profit_transaction.applied)
        
        print("✅ Deposit profit transaction creation working correctly!")

    def run_all_tests(self):
        """Run all deposit model tests"""
        print("=" * 80)
        print("DEPOSIT MODEL TESTS")
        print("=" * 80)
        
        try:
            self.test_deposit_creation()
            self.test_deposit_balance_calculation()
            self.test_deposit_profit_calculation()
            self.test_deposit_funding_sources()
            self.test_deposit_validation()
            self.test_deposit_string_representation()
            self.test_deposit_profit_transaction_creation()
            
            print("\n" + "=" * 80)
            print("✅ ALL DEPOSIT MODEL TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = DepositModelTest()
    test.setUp()
    test.run_all_tests()
