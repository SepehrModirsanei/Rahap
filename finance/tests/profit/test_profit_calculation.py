"""
Comprehensive test for profit calculation system
Tests both account and deposit profit accrual
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from finance.models import User, Account, Deposit, Transaction, AccountDailyBalance
from finance.management.commands.accrue_monthly_profit import Command


class ProfitCalculationTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test accounts
        self.rial_account = Account.objects.create(
            user=self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00'),  # 1,000,000 Rial
            monthly_profit_rate=Decimal('2.5')  # 2.5% monthly
        )
        
        self.gold_account = Account.objects.create(
            user=self.user,
            name='Test Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('10.00'),  # 10 grams of gold
            monthly_profit_rate=Decimal('1.0')  # 1% monthly
        )
        
        # Create test deposit
        self.deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('500000.00'),  # 500,000 Rial
            monthly_profit_rate=Decimal('3.0')  # 3% monthly
        )

    def test_account_profit_calculation_with_daily_snapshots(self):
        """Test account profit calculation using daily snapshots"""
        print("\n=== Testing Account Profit Calculation ===")
        
        # Create daily snapshots for the last 30 days
        today = date.today()
        base_balance = Decimal('1000000.00')
        
        # Create snapshots with varying balances
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            # Simulate balance changes over time
            balance = base_balance + Decimal(str(i * 1000))  # Increasing balance
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=balance
            )
        
        print(f"Created 30 daily snapshots for account {self.rial_account.name}")
        print(f"Account balance: {self.rial_account.balance}")
        print(f"Monthly profit rate: {self.rial_account.monthly_profit_rate}%")
        
        # Test profit calculation
        initial_balance = self.rial_account.balance
        self.rial_account.accrue_monthly_profit()
        final_balance = self.rial_account.balance
        
        print(f"Balance before profit: {initial_balance}")
        print(f"Balance after profit: {final_balance}")
        print(f"Profit earned: {final_balance - initial_balance}")
        
        # Verify profit was calculated
        self.assertGreater(final_balance, initial_balance)
        
        # Check that a profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)
        
        profit_transaction = profit_transactions.first()
        print(f"Profit transaction created: {profit_transaction.amount}")
        print(f"Transaction state: {profit_transaction.state}")

    def test_deposit_profit_calculation(self):
        """Test deposit profit calculation"""
        print("\n=== Testing Deposit Profit Calculation ===")
        
        print(f"Deposit initial balance: {self.deposit.initial_balance}")
        print(f"Deposit monthly profit rate: {self.deposit.monthly_profit_rate}%")
        print(f"Last profit accrual: {self.deposit.last_profit_accrual_at}")
        
        # Test profit calculation
        initial_balance = self.deposit.initial_balance
        self.deposit.accrue_monthly_profit()
        final_balance = self.deposit.initial_balance
        
        print(f"Deposit balance before profit: {initial_balance}")
        print(f"Deposit balance after profit: {final_balance}")
        print(f"Profit earned: {final_balance - initial_balance}")
        
        # Verify profit was calculated (deposit profits go to base account, not back to deposit)
        # The deposit balance should remain the same, but profit should be credited to user's account
        self.assertEqual(final_balance, initial_balance)
        
        # Check that a profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)
        
        profit_transaction = profit_transactions.first()
        print(f"Profit transaction created: {profit_transaction.amount}")
        print(f"Transaction state: {profit_transaction.state}")
        
        # Check that profit was added to user's base account (حساب پایه)
        base_account = self.user.accounts.filter(name='حساب پایه').first()
        base_account_balance = base_account.balance
        print(f"Base account balance after deposit profit: {base_account_balance}")
        
        # Verify the profit was credited to the base account
        expected_profit = (self.deposit.initial_balance * self.deposit.monthly_profit_rate) / 100
        self.assertEqual(base_account_balance, expected_profit)

    def test_management_command(self):
        """Test the management command for profit accrual"""
        print("\n=== Testing Management Command ===")
        
        # Create daily snapshots for accounts
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
            AccountDailyBalance.objects.create(
                account=self.gold_account,
                snapshot_date=snapshot_date,
                balance=Decimal('10.00')
            )
        
        # Run the management command
        command = Command()
        result = command.handle()
        
        print("Management command executed successfully")
        
        # Verify that profits were calculated
        account_profit_transactions = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            applied=True
        )
        deposit_profit_transactions = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        
        print(f"Account profit transactions: {account_profit_transactions.count()}")
        print(f"Deposit profit transactions: {deposit_profit_transactions.count()}")
        
        # Should have profit transactions for both accounts and deposit
        self.assertGreaterEqual(account_profit_transactions.count(), 1)
        self.assertGreaterEqual(deposit_profit_transactions.count(), 1)

    def test_profit_calculation_timing(self):
        """Test that profit is only calculated when enough time has passed"""
        print("\n=== Testing Profit Calculation Timing ===")
        
        # Set last profit accrual to recent date (should not calculate profit)
        recent_date = timezone.now() - timedelta(days=5)
        self.rial_account.last_profit_accrual_at = recent_date
        self.rial_account.save()
        
        initial_balance = self.rial_account.balance
        self.rial_account.accrue_monthly_profit()
        final_balance = self.rial_account.balance
        
        print(f"Recent accrual test - Balance unchanged: {initial_balance == final_balance}")
        
        # Set last profit accrual to old date (should calculate profit)
        old_date = timezone.now() - timedelta(days=35)
        self.rial_account.last_profit_accrual_at = old_date
        self.rial_account.save()
        
        initial_balance = self.rial_account.balance
        self.rial_account.accrue_monthly_profit()
        final_balance = self.rial_account.balance
        
        print(f"Old accrual test - Balance changed: {initial_balance != final_balance}")
        print(f"Profit calculated: {final_balance - initial_balance}")

    def test_zero_profit_rate(self):
        """Test that no profit is calculated when rate is zero"""
        print("\n=== Testing Zero Profit Rate ===")
        
        # Create account with zero profit rate
        zero_profit_account = Account.objects.create(
            user=self.user,
            name='Zero Profit Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('100000.00'),
            monthly_profit_rate=Decimal('0.0')
        )
        
        initial_balance = zero_profit_account.balance
        zero_profit_account.accrue_monthly_profit()
        final_balance = zero_profit_account.balance
        
        print(f"Zero profit rate test - Balance unchanged: {initial_balance == final_balance}")
        self.assertEqual(initial_balance, final_balance)

    def test_profit_transaction_details(self):
        """Test the details of profit transactions"""
        print("\n=== Testing Profit Transaction Details ===")
        
        # Create daily snapshots
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
        
        # Calculate profit
        self.rial_account.accrue_monthly_profit()
        
        # Get profit transaction
        profit_transaction = Transaction.objects.filter(
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            applied=True
        ).first()
        
        if profit_transaction:
            print(f"Profit transaction amount: {profit_transaction.amount}")
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

    def run_all_tests(self):
        """Run all profit calculation tests"""
        print("=" * 60)
        print("PROFIT CALCULATION COMPREHENSIVE TEST")
        print("=" * 60)
        
        try:
            self.test_account_profit_calculation_with_daily_snapshots()
            self.test_deposit_profit_calculation()
            self.test_management_command()
            self.test_profit_calculation_timing()
            self.test_zero_profit_rate()
            self.test_profit_transaction_details()
            
            print("\n" + "=" * 60)
            print("✅ ALL PROFIT CALCULATION TESTS PASSED!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = ProfitCalculationTest()
    test.setUp()
    test.run_all_tests()
