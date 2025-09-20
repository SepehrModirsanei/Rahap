"""
Complete test of the profit calculation system
Demonstrates both account and deposit profit calculation with transaction creation
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from finance.models import User, Account, Deposit, Transaction, AccountDailyBalance
from finance.management.commands.accrue_monthly_profit import Command


class CompleteProfitSystemTest(TestCase):
    def setUp(self):
        """Set up comprehensive test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create accounts with different profit rates
        self.rial_account1 = Account.objects.create(
            user=self.user1,
            name='User1 Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('2000000.00'),  # 2,000,000 Rial
            monthly_profit_rate=Decimal('3.0')  # 3% monthly
        )
        
        self.gold_account1 = Account.objects.create(
            user=self.user1,
            name='User1 Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('20.00'),  # 20 grams of gold
            monthly_profit_rate=Decimal('1.5')  # 1.5% monthly
        )
        
        self.rial_account2 = Account.objects.create(
            user=self.user2,
            name='User2 Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00'),  # 1,000,000 Rial
            monthly_profit_rate=Decimal('2.0')  # 2% monthly
        )
        
        # Create deposits with different profit rates
        self.deposit1 = Deposit.objects.create(
            user=self.user1,
            initial_balance=Decimal('1000000.00'),  # 1,000,000 Rial
            monthly_profit_rate=Decimal('4.0')  # 4% monthly
        )
        
        self.deposit2 = Deposit.objects.create(
            user=self.user2,
            initial_balance=Decimal('500000.00'),  # 500,000 Rial
            monthly_profit_rate=Decimal('2.5')  # 2.5% monthly
        )

    def test_complete_profit_system(self):
        """Test the complete profit calculation system"""
        print("\n" + "=" * 80)
        print("COMPLETE PROFIT CALCULATION SYSTEM TEST")
        print("=" * 80)
        
        # Create daily snapshots for all accounts
        today = date.today()
        print(f"Creating daily snapshots for the last 30 days (ending {today})")
        
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            
            # Create snapshots for all accounts
            AccountDailyBalance.objects.create(
                account=self.rial_account1,
                snapshot_date=snapshot_date,
                balance=Decimal('2000000.00')
            )
            AccountDailyBalance.objects.create(
                account=self.gold_account1,
                snapshot_date=snapshot_date,
                balance=Decimal('20.00')
            )
            AccountDailyBalance.objects.create(
                account=self.rial_account2,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
        
        print("✅ Daily snapshots created successfully")
        
        # Show initial state
        print("\n--- INITIAL STATE ---")
        print(f"User1 Rial Account: {self.rial_account1.balance} (Rate: {self.rial_account1.monthly_profit_rate}%)")
        print(f"User1 Gold Account: {self.gold_account1.balance} (Rate: {self.gold_account1.monthly_profit_rate}%)")
        print(f"User2 Rial Account: {self.rial_account2.balance} (Rate: {self.rial_account2.monthly_profit_rate}%)")
        print(f"User1 Deposit: {self.deposit1.initial_balance} (Rate: {self.deposit1.monthly_profit_rate}%)")
        print(f"User2 Deposit: {self.deposit2.initial_balance} (Rate: {self.deposit2.monthly_profit_rate}%)")
        
        # Count initial transactions
        initial_transaction_count = Transaction.objects.count()
        print(f"\nInitial transaction count: {initial_transaction_count}")
        
        # Run the management command
        print("\n--- RUNNING PROFIT ACCRUAL COMMAND ---")
        command = Command()
        result = command.handle()
        print(f"Command result: {result}")
        
        # Show final state
        print("\n--- FINAL STATE ---")
        print(f"User1 Rial Account: {self.rial_account1.balance} (Last accrual: {self.rial_account1.last_profit_accrual_at})")
        print(f"User1 Gold Account: {self.gold_account1.balance} (Last accrual: {self.gold_account1.last_profit_accrual_at})")
        print(f"User2 Rial Account: {self.rial_account2.balance} (Last accrual: {self.rial_account2.last_profit_accrual_at})")
        print(f"User1 Deposit: {self.deposit1.initial_balance} (Last accrual: {self.deposit1.last_profit_accrual_at})")
        print(f"User2 Deposit: {self.deposit2.initial_balance} (Last accrual: {self.deposit2.last_profit_accrual_at})")
        
        # Count final transactions
        final_transaction_count = Transaction.objects.count()
        print(f"\nFinal transaction count: {final_transaction_count}")
        print(f"New transactions created: {final_transaction_count - initial_transaction_count}")
        
        # Show all profit transactions
        print("\n--- PROFIT TRANSACTIONS CREATED ---")
        account_profit_txns = Transaction.objects.filter(kind=Transaction.KIND_PROFIT_ACCOUNT, applied=True)
        deposit_profit_txns = Transaction.objects.filter(kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT, applied=True)
        
        print(f"Account profit transactions: {account_profit_txns.count()}")
        for txn in account_profit_txns:
            print(f"  - ID: {txn.id}, User: {txn.user.username}, Amount: {txn.amount}, Account: {txn.destination_account.name}")
        
        print(f"Deposit profit transactions: {deposit_profit_txns.count()}")
        for txn in deposit_profit_txns:
            print(f"  - ID: {txn.id}, User: {txn.user.username}, Amount: {txn.amount}, Destination: {txn.destination_account.name}")
        
        # Verify results
        print("\n--- VERIFICATION ---")
        
        # Verify account profits were calculated
        self.assertGreater(self.rial_account1.balance, Decimal('2000000.00'))
        self.assertGreater(self.gold_account1.balance, Decimal('20.00'))
        self.assertGreater(self.rial_account2.balance, Decimal('1000000.00'))
        
        # Verify deposit profits were calculated (deposits don't compound, profit goes to account)
        # The deposit balance should remain the same, but profit should be credited to user's account
        self.assertEqual(self.deposit1.initial_balance, Decimal('1000000.00'))
        self.assertEqual(self.deposit2.initial_balance, Decimal('500000.00'))
        
        # Verify transactions were created
        self.assertGreaterEqual(account_profit_txns.count(), 3)  # At least 3 account profit transactions
        self.assertGreaterEqual(deposit_profit_txns.count(), 2)  # At least 2 deposit profit transactions
        
        # Verify all profit transactions are applied
        all_profit_txns = list(account_profit_txns) + list(deposit_profit_txns)
        for txn in all_profit_txns:
            self.assertTrue(txn.applied)
            self.assertEqual(txn.state, Transaction.STATE_DONE)
            self.assertGreater(txn.amount, 0)
        
        print("✅ All verifications passed!")
        
        # Calculate total profits
        total_account_profit = sum(txn.amount for txn in account_profit_txns)
        total_deposit_profit = sum(txn.amount for txn in deposit_profit_txns)
        
        print(f"\n--- PROFIT SUMMARY ---")
        print(f"Total account profits: {total_account_profit}")
        print(f"Total deposit profits: {total_deposit_profit}")
        print(f"Total profits: {total_account_profit + total_deposit_profit}")
        
        return {
            'account_profit_txns': account_profit_txns.count(),
            'deposit_profit_txns': deposit_profit_txns.count(),
            'total_account_profit': total_account_profit,
            'total_deposit_profit': total_deposit_profit
        }

    def test_profit_calculation_accuracy(self):
        """Test that profit calculations are accurate"""
        print("\n" + "=" * 80)
        print("PROFIT CALCULATION ACCURACY TEST")
        print("=" * 80)
        
        # Create daily snapshots
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            AccountDailyBalance.objects.create(
                account=self.rial_account1,
                snapshot_date=snapshot_date,
                balance=Decimal('2000000.00')
            )
        
        # Calculate expected profit
        expected_profit = (Decimal('2000000.00') * Decimal('3.0')) / Decimal('100')
        print(f"Expected profit (3% of 2,000,000): {expected_profit}")
        
        # Calculate actual profit
        initial_balance = self.rial_account1.balance
        self.rial_account1.accrue_monthly_profit()
        final_balance = self.rial_account1.balance
        actual_profit = final_balance - initial_balance
        
        print(f"Actual profit: {actual_profit}")
        print(f"Difference: {abs(actual_profit - expected_profit)}")
        
        # Verify accuracy (allow small rounding differences)
        self.assertAlmostEqual(float(actual_profit), float(expected_profit), places=2)
        
        print("✅ Profit calculation is accurate!")

    def run_all_tests(self):
        """Run all comprehensive profit system tests"""
        try:
            results = self.test_complete_profit_system()
            self.test_profit_calculation_accuracy()
            
            print("\n" + "=" * 80)
            print("✅ ALL COMPREHENSIVE PROFIT SYSTEM TESTS PASSED!")
            print("=" * 80)
            print(f"Account profit transactions: {results['account_profit_txns']}")
            print(f"Deposit profit transactions: {results['deposit_profit_txns']}")
            print(f"Total account profits: {results['total_account_profit']}")
            print(f"Total deposit profits: {results['total_deposit_profit']}")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = CompleteProfitSystemTest()
    test.setUp()
    test.run_all_tests()
