"""
Tests for User model functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from finance.models import Account, Deposit, Transaction


class UserModelTest(TestCase):
    """Test User model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_creation_creates_base_account(self):
        """Test that creating a user automatically creates a base account"""
        print("\n=== Testing User Base Account Creation ===")
        
        # Check that base account was created
        base_account = self.user.accounts.filter(name='حساب پایه').first()
        self.assertIsNotNone(base_account)
        print(f"Base account created: {base_account.name}")
        print(f"Base account type: {base_account.account_type}")
        print(f"Base account balance: {base_account.balance}")
        
        # Verify account properties
        self.assertEqual(base_account.account_type, Account.ACCOUNT_TYPE_RIAL)
        self.assertEqual(base_account.initial_balance, Decimal('0.00'))
        self.assertEqual(base_account.monthly_profit_rate, Decimal('0.00'))
        
        print("✅ User base account created correctly!")

    def test_user_short_user_id(self):
        """Test that user has a short_user_id property"""
        print("\n=== Testing User Short ID ===")
        
        # Check that user has user_id
        self.assertIsNotNone(self.user.user_id)
        print(f"User ID: {self.user.user_id}")
        
        # Check short_user_id property
        short_id = self.user.short_user_id
        self.assertIsNotNone(short_id)
        self.assertEqual(len(short_id), 8)  # First 8 characters
        self.assertEqual(short_id, str(self.user.user_id)[:8])
        print(f"Short user ID: {short_id}")
        
        print("✅ User short ID working correctly!")

    def test_user_account_relationship(self):
        """Test user-account relationship"""
        print("\n=== Testing User-Account Relationship ===")
        
        # Create additional accounts
        rial_account = Account.objects.create(
            user=self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )
        
        gold_account = Account.objects.create(
            user=self.user,
            name='Test Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('10.00')
        )
        
        # Check account count
        account_count = self.user.accounts.count()
        print(f"Total accounts for user: {account_count}")
        self.assertEqual(account_count, 3)  # Base account + 2 created accounts
        
        # Check account types
        account_types = list(self.user.accounts.values_list('account_type', flat=True))
        print(f"Account types: {account_types}")
        self.assertIn(Account.ACCOUNT_TYPE_RIAL, account_types)
        self.assertIn(Account.ACCOUNT_TYPE_GOLD, account_types)
        
        print("✅ User-account relationship working correctly!")

    def test_user_deposit_relationship(self):
        """Test user-deposit relationship"""
        print("\n=== Testing User-Deposit Relationship ===")
        
        # Create deposits
        deposit1 = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('500000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        deposit2 = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('2.5')
        )
        
        # Check deposit count
        deposit_count = self.user.deposits.count()
        print(f"Total deposits for user: {deposit_count}")
        self.assertEqual(deposit_count, 2)
        
        # Check deposit properties
        for deposit in self.user.deposits.all():
            print(f"Deposit: {deposit.initial_balance}, Rate: {deposit.monthly_profit_rate}%")
            self.assertEqual(deposit.user, self.user)
        
        print("✅ User-deposit relationship working correctly!")

    def test_user_transaction_relationship(self):
        """Test user-transaction relationship"""
        print("\n=== Testing User-Transaction Relationship ===")
        
        # Get base account
        base_account = self.user.accounts.filter(name='حساب پایه').first()
        
        # Create transactions
        transaction1 = Transaction.objects.create(
            user=self.user,
            destination_account=base_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        transaction2 = Transaction.objects.create(
            user=self.user,
            destination_account=base_account,
            amount=Decimal('50000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        # Check transaction count
        transaction_count = self.user.transactions.count()
        print(f"Total transactions for user: {transaction_count}")
        self.assertEqual(transaction_count, 2)
        
        # Check transaction properties
        for transaction in self.user.transactions.all():
            print(f"Transaction: {transaction.amount}, Kind: {transaction.kind}")
            self.assertEqual(transaction.user, self.user)
        
        print("✅ User-transaction relationship working correctly!")

    def run_all_tests(self):
        """Run all user model tests"""
        print("=" * 80)
        print("USER MODEL TESTS")
        print("=" * 80)
        
        try:
            self.test_user_creation_creates_base_account()
            self.test_user_short_user_id()
            self.test_user_account_relationship()
            self.test_user_deposit_relationship()
            self.test_user_transaction_relationship()
            
            print("\n" + "=" * 80)
            print("✅ ALL USER MODEL TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = UserModelTest()
    test.setUp()
    test.run_all_tests()
