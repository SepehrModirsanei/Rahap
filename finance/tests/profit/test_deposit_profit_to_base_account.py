"""
Test to verify that deposit profits are sent to the user's base account (حساب پایه)
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from finance.models import User, Account, Deposit, Transaction


class DepositProfitToBaseAccountTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get the default base account created by User model
        self.base_account = self.user.accounts.filter(name='حساب پایه').first()
        # Set initial balance for testing
        self.base_account.initial_balance = Decimal('1000000.00')
        self.base_account.save()
        
        # Create another rial account (not the base account)
        self.other_account = Account.objects.create(
            user=self.user,
            name='Other Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('500000.00')  # 500,000 Rial
        )
        
        # Create test deposit
        self.deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('2000000.00'),  # 2,000,000 Rial
            monthly_profit_rate=Decimal('3.0')  # 3% monthly
        )

    def test_deposit_profit_goes_to_base_account(self):
        """Test that deposit profit goes to the user's base account (حساب پایه)"""
        print("\n=== Testing Deposit Profit to Base Account ===")
        
        # Get initial balances
        initial_base_balance = self.base_account.balance
        initial_other_balance = self.other_account.balance
        initial_deposit_balance = self.deposit.initial_balance
        
        print(f"Initial base account balance: {initial_base_balance}")
        print(f"Initial other account balance: {initial_other_balance}")
        print(f"Initial deposit balance: {initial_deposit_balance}")
        
        # Calculate expected profit
        expected_profit = (self.deposit.initial_balance * self.deposit.monthly_profit_rate) / 100
        print(f"Expected profit (3% of 2,000,000): {expected_profit}")
        
        # Calculate deposit profit
        self.deposit.accrue_monthly_profit()
        
        # Get final balances
        final_base_balance = self.base_account.balance
        final_other_balance = self.other_account.balance
        final_deposit_balance = self.deposit.initial_balance
        
        print(f"Final base account balance: {final_base_balance}")
        print(f"Final other account balance: {final_other_balance}")
        print(f"Final deposit balance: {final_deposit_balance}")
        
        # Verify that profit went to base account
        base_account_profit = final_base_balance - initial_base_balance
        other_account_profit = final_other_balance - initial_other_balance
        
        print(f"Base account profit: {base_account_profit}")
        print(f"Other account profit: {other_account_profit}")
        
        # The profit should go to the base account, not the other account
        self.assertEqual(base_account_profit, expected_profit)
        self.assertEqual(other_account_profit, Decimal('0.00'))
        
        # Verify the profit transaction was created correctly
        profit_transaction = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        self.assertIsNotNone(profit_transaction)
        print(f"Profit transaction destination: {profit_transaction.destination_account.name}")
        print(f"Profit transaction amount: {profit_transaction.amount}")
        
        # Verify the transaction goes to the base account
        self.assertEqual(profit_transaction.destination_account, self.base_account)
        self.assertEqual(profit_transaction.amount, expected_profit)
        
        print("✅ Deposit profit correctly sent to base account!")

    def test_deposit_profit_creates_base_account_if_none_exists(self):
        """Test that a base account is created if none exists"""
        print("\n=== Testing Base Account Creation ===")
        
        # Create a new user without any accounts
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        
        # Create a deposit for this user
        new_deposit = Deposit.objects.create(
            user=new_user,
            initial_balance=Decimal('1000000.00'),  # 1,000,000 Rial
            monthly_profit_rate=Decimal('2.5')  # 2.5% monthly
        )
        
        # Verify only the default base account exists initially
        initial_account_count = new_user.accounts.count()
        print(f"Initial account count: {initial_account_count}")
        self.assertEqual(initial_account_count, 1)  # User model creates default base account
        
        # Calculate deposit profit (should create base account)
        new_deposit.accrue_monthly_profit()
        
        # Verify still only one account (the default base account)
        final_account_count = new_user.accounts.count()
        print(f"Final account count: {final_account_count}")
        self.assertEqual(final_account_count, 1)  # Should still be 1 (default base account)
        
        # Verify the created account is the base account
        base_account = new_user.accounts.first()
        print(f"Created account name: {base_account.name}")
        print(f"Created account type: {base_account.account_type}")
        print(f"Created account balance: {base_account.balance}")
        
        self.assertEqual(base_account.name, 'حساب پایه')
        self.assertEqual(base_account.account_type, Account.ACCOUNT_TYPE_RIAL)
        
        # Verify the profit was credited to the base account
        expected_profit = (new_deposit.initial_balance * new_deposit.monthly_profit_rate) / 100
        self.assertEqual(base_account.balance, expected_profit)
        
        print("✅ Base account created and profit credited correctly!")

    def test_multiple_deposits_profit_to_same_base_account(self):
        """Test that multiple deposits send profit to the same base account"""
        print("\n=== Testing Multiple Deposits to Same Base Account ===")
        
        # Create multiple deposits for the same user
        deposit1 = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),  # 1,000,000 Rial
            monthly_profit_rate=Decimal('2.0')  # 2% monthly
        )
        
        deposit2 = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('500000.00'),  # 500,000 Rial
            monthly_profit_rate=Decimal('3.0')  # 3% monthly
        )
        
        # Get initial base account balance
        initial_base_balance = self.base_account.balance
        print(f"Initial base account balance: {initial_base_balance}")
        
        # Calculate profits for both deposits
        deposit1.accrue_monthly_profit()
        deposit2.accrue_monthly_profit()
        
        # Get final base account balance
        final_base_balance = self.base_account.balance
        print(f"Final base account balance: {final_base_balance}")
        
        # Calculate expected total profit
        expected_profit1 = (deposit1.initial_balance * deposit1.monthly_profit_rate) / 100
        expected_profit2 = (deposit2.initial_balance * deposit2.monthly_profit_rate) / 100
        expected_total_profit = expected_profit1 + expected_profit2
        
        print(f"Expected profit from deposit1: {expected_profit1}")
        print(f"Expected profit from deposit2: {expected_profit2}")
        print(f"Expected total profit: {expected_total_profit}")
        
        # Verify total profit was credited to base account
        actual_total_profit = final_base_balance - initial_base_balance
        print(f"Actual total profit: {actual_total_profit}")
        
        self.assertEqual(actual_total_profit, expected_total_profit)
        
        # Verify both profit transactions go to the base account
        profit_transactions = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        
        self.assertEqual(profit_transactions.count(), 2)
        
        for txn in profit_transactions:
            self.assertEqual(txn.destination_account, self.base_account)
            print(f"Transaction {txn.id}: Amount {txn.amount}, Destination: {txn.destination_account.name}")
        
        print("✅ Multiple deposits correctly send profit to same base account!")

    def run_all_tests(self):
        """Run all deposit profit to base account tests"""
        print("=" * 80)
        print("DEPOSIT PROFIT TO BASE ACCOUNT TEST")
        print("=" * 80)
        
        try:
            self.test_deposit_profit_goes_to_base_account()
            self.test_deposit_profit_creates_base_account_if_none_exists()
            self.test_multiple_deposits_profit_to_same_base_account()
            
            print("\n" + "=" * 80)
            print("✅ ALL DEPOSIT PROFIT TO BASE ACCOUNT TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = DepositProfitToBaseAccountTest()
    test.setUp()
    test.run_all_tests()
