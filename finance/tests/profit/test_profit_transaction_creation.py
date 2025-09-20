"""
Test to verify that profit transactions are created correctly
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from finance.models import User, Account, Deposit, Transaction, AccountDailyBalance


class ProfitTransactionCreationTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test account with profit rate
        self.rial_account = Account.objects.create(
            user=self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00'),  # 1,000,000 Rial
            monthly_profit_rate=Decimal('2.5')  # 2.5% monthly
        )
        
        # Create test deposit with profit rate
        self.deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('500000.00'),  # 500,000 Rial
            monthly_profit_rate=Decimal('3.0')  # 3% monthly
        )

    def test_account_profit_transaction_creation(self):
        """Test that profit transactions are created for accounts"""
        print("\n=== Testing Account Profit Transaction Creation ===")
        
        # Create daily snapshots for the last 30 days
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
        
        # Count transactions before profit calculation
        initial_transaction_count = Transaction.objects.count()
        print(f"Initial transaction count: {initial_transaction_count}")
        
        # Calculate profit
        self.rial_account.accrue_monthly_profit()
        
        # Count transactions after profit calculation
        final_transaction_count = Transaction.objects.count()
        print(f"Final transaction count: {final_transaction_count}")
        
        # Verify a new transaction was created
        self.assertEqual(final_transaction_count, initial_transaction_count + 1)
        
        # Get the profit transaction
        profit_transaction = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            applied=True
        ).first()
        
        self.assertIsNotNone(profit_transaction)
        print(f"Profit transaction created: ID={profit_transaction.id}")
        print(f"Transaction amount: {profit_transaction.amount}")
        print(f"Transaction state: {profit_transaction.state}")
        print(f"Transaction applied: {profit_transaction.applied}")
        print(f"Source account: {profit_transaction.source_account}")
        print(f"Destination account: {profit_transaction.destination_account}")
        print(f"Transaction kind: {profit_transaction.get_kind_display()}")
        
        # Verify transaction details
        self.assertEqual(profit_transaction.user, self.user)
        self.assertEqual(profit_transaction.destination_account, self.rial_account)
        self.assertEqual(profit_transaction.state, Transaction.STATE_DONE)
        self.assertTrue(profit_transaction.applied)
        self.assertGreater(profit_transaction.amount, 0)
        self.assertIsNone(profit_transaction.source_account)  # Profit has no source

    def test_deposit_profit_transaction_creation(self):
        """Test that profit transactions are created for deposits"""
        print("\n=== Testing Deposit Profit Transaction Creation ===")
        
        # Count transactions before profit calculation
        initial_transaction_count = Transaction.objects.count()
        print(f"Initial transaction count: {initial_transaction_count}")
        
        # Calculate profit
        self.deposit.accrue_monthly_profit()
        
        # Count transactions after profit calculation
        final_transaction_count = Transaction.objects.count()
        print(f"Final transaction count: {final_transaction_count}")
        
        # Verify a new transaction was created
        self.assertEqual(final_transaction_count, initial_transaction_count + 1)
        
        # Get the profit transaction
        profit_transaction = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        self.assertIsNotNone(profit_transaction)
        print(f"Profit transaction created: ID={profit_transaction.id}")
        print(f"Transaction amount: {profit_transaction.amount}")
        print(f"Transaction state: {profit_transaction.state}")
        print(f"Transaction applied: {profit_transaction.applied}")
        print(f"Source account: {profit_transaction.source_account}")
        print(f"Destination account: {profit_transaction.destination_account}")
        print(f"Transaction kind: {profit_transaction.get_kind_display()}")
        
        # Verify transaction details
        self.assertEqual(profit_transaction.user, self.user)
        self.assertEqual(profit_transaction.state, Transaction.STATE_DONE)
        self.assertTrue(profit_transaction.applied)
        self.assertGreater(profit_transaction.amount, 0)
        self.assertIsNone(profit_transaction.source_account)  # Profit has no source
        
        # Verify destination is user's rial account
        self.assertEqual(profit_transaction.destination_account.account_type, Account.ACCOUNT_TYPE_RIAL)

    def test_profit_transaction_kinds(self):
        """Test that different profit transaction kinds are created"""
        print("\n=== Testing Profit Transaction Kinds ===")
        
        # Create daily snapshots for account
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
        
        # Calculate account profit
        self.rial_account.accrue_monthly_profit()
        
        # Calculate deposit profit
        self.deposit.accrue_monthly_profit()
        
        # Check account profit transaction
        account_profit_txn = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_ACCOUNT
        ).first()
        
        self.assertIsNotNone(account_profit_txn)
        print(f"Account profit transaction kind: {account_profit_txn.kind}")
        print(f"Account profit transaction display: {account_profit_txn.get_kind_display()}")
        
        # Check deposit profit transaction
        deposit_profit_txn = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT
        ).first()
        
        self.assertIsNotNone(deposit_profit_txn)
        print(f"Deposit profit transaction kind: {deposit_profit_txn.kind}")
        print(f"Deposit profit transaction display: {deposit_profit_txn.get_kind_display()}")
        
        # Verify they are different kinds
        self.assertNotEqual(account_profit_txn.kind, deposit_profit_txn.kind)

    def test_profit_transaction_application(self):
        """Test that profit transactions are properly applied"""
        print("\n=== Testing Profit Transaction Application ===")
        
        # Create daily snapshots for account
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
        
        # Get initial balance
        initial_balance = self.rial_account.balance
        print(f"Initial account balance: {initial_balance}")
        
        # Calculate profit
        self.rial_account.accrue_monthly_profit()
        
        # Get final balance
        final_balance = self.rial_account.balance
        print(f"Final account balance: {final_balance}")
        
        # Get profit transaction
        profit_transaction = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            applied=True
        ).first()
        
        self.assertIsNotNone(profit_transaction)
        print(f"Profit transaction amount: {profit_transaction.amount}")
        print(f"Balance increase: {final_balance - initial_balance}")
        
        # Verify that the balance increase matches the transaction amount
        self.assertEqual(final_balance - initial_balance, profit_transaction.amount)
        
        # Verify transaction is applied
        self.assertTrue(profit_transaction.applied)
        self.assertEqual(profit_transaction.state, Transaction.STATE_DONE)

    def run_all_tests(self):
        """Run all profit transaction creation tests"""
        print("=" * 60)
        print("PROFIT TRANSACTION CREATION TEST")
        print("=" * 60)
        
        try:
            self.test_account_profit_transaction_creation()
            self.test_deposit_profit_transaction_creation()
            self.test_profit_transaction_kinds()
            self.test_profit_transaction_application()
            
            print("\n" + "=" * 60)
            print("✅ ALL PROFIT TRANSACTION TESTS PASSED!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = ProfitTransactionCreationTest()
    test.setUp()
    test.run_all_tests()
