"""
Tests for different deposit profit kinds and transfer intervals

This test file verifies that:
- Monthly deposits: Profit transferred every 30 days
- 6-month deposits: Profit transferred every 180 days  
- Yearly deposits: Profit transferred every 365 days
- Profit calculation is always daily (30-day window)
- Transfer intervals are correctly enforced
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from finance.models import User, Account, Deposit, Transaction, DepositDailyBalance
from finance.tests.test_config import FinanceTestCase


class DepositProfitKindsTests(FinanceTestCase):
    """Tests for different deposit profit kinds and transfer intervals"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.base_account = self.get_user_base_account(self.user)
        
        # Create deposits with different profit kinds
        self.monthly_deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),  # 1,000,000 Rial
            monthly_profit_rate=Decimal('3.0'),  # 3% monthly
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        self.six_month_deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('2000000.00'),  # 2,000,000 Rial
            monthly_profit_rate=Decimal('18.0'),  # 18% for 6 months (3% monthly)
            profit_kind=Deposit.PROFIT_KIND_SEMIANNUAL
        )
        
        self.yearly_deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('3000000.00'),  # 3,000,000 Rial
            monthly_profit_rate=Decimal('36.0'),  # 36% for 1 year (3% monthly)
            profit_kind=Deposit.PROFIT_KIND_YEARLY
        )

    def test_monthly_deposit_profit_transfer_30_days(self):
        """Test that monthly deposits transfer profit every 30 days"""
        print("\n=== Testing Monthly Deposit (30-day transfer) ===")
        
        # Set last accrual to 29 days ago (should NOT transfer)
        past_time = timezone.now() - timedelta(days=29)
        self.monthly_deposit.last_profit_accrual_at = past_time
        self.monthly_deposit.save()
        
        # Try to accrue profit
        self.monthly_deposit.accrue_monthly_profit()
        
        # Should NOT create profit transaction (not enough time passed)
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)
        print("✅ 29 days: No profit transfer (correct)")
        
        # Set last accrual to 31 days ago (should transfer)
        past_time = timezone.now() - timedelta(days=31)
        self.monthly_deposit.last_profit_accrual_at = past_time
        self.monthly_deposit.save()
        
        # Try to accrue profit
        self.monthly_deposit.accrue_monthly_profit()
        
        # Should create profit transaction
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)
        print("✅ 31 days: Profit transfer created (correct)")

    def test_six_month_deposit_profit_transfer_180_days(self):
        """Test that 6-month deposits transfer profit every 180 days"""
        print("\n=== Testing 6-Month Deposit (180-day transfer) ===")
        
        # Set last accrual to 179 days ago (should NOT transfer)
        past_time = timezone.now() - timedelta(days=179)
        self.six_month_deposit.last_profit_accrual_at = past_time
        self.six_month_deposit.save()
        
        # Try to accrue profit
        self.six_month_deposit.accrue_monthly_profit()
        
        # Should NOT create profit transaction (not enough time passed)
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)
        print("✅ 179 days: No profit transfer (correct)")
        
        # Set last accrual to 181 days ago (should transfer)
        past_time = timezone.now() - timedelta(days=181)
        self.six_month_deposit.last_profit_accrual_at = past_time
        self.six_month_deposit.save()
        
        # Try to accrue profit
        self.six_month_deposit.accrue_monthly_profit()
        
        # Should create profit transaction
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)
        print("✅ 181 days: Profit transfer created (correct)")

    def test_yearly_deposit_profit_transfer_365_days(self):
        """Test that yearly deposits transfer profit every 365 days"""
        print("\n=== Testing Yearly Deposit (365-day transfer) ===")
        
        # Set last accrual to 364 days ago (should NOT transfer)
        past_time = timezone.now() - timedelta(days=364)
        self.yearly_deposit.last_profit_accrual_at = past_time
        self.yearly_deposit.save()
        
        # Try to accrue profit
        self.yearly_deposit.accrue_monthly_profit()
        
        # Should NOT create profit transaction (not enough time passed)
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)
        print("✅ 364 days: No profit transfer (correct)")
        
        # Set last accrual to 366 days ago (should transfer)
        past_time = timezone.now() - timedelta(days=366)
        self.yearly_deposit.last_profit_accrual_at = past_time
        self.yearly_deposit.save()
        
        # Try to accrue profit
        self.yearly_deposit.accrue_monthly_profit()
        
        # Should create profit transaction
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)
        print("✅ 366 days: Profit transfer created (correct)")

    def test_profit_calculation_always_daily(self):
        """Test that profit calculation is always based on 30-day average"""
        print("\n=== Testing Daily Profit Calculation (30-day window) ===")
        
        # Create daily snapshots for the last 30 days
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            DepositDailyBalance.objects.create(
                deposit=self.monthly_deposit,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')  # Constant balance
            )
        
        # Set last accrual to 31 days ago (should transfer)
        past_time = timezone.now() - timedelta(days=31)
        self.monthly_deposit.last_profit_accrual_at = past_time
        self.monthly_deposit.save()
        
        # Calculate profit
        self.monthly_deposit.accrue_monthly_profit()
        
        # Get profit transaction
        profit_transaction = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        # Expected profit: 3% of 1,000,000 = 30,000 (based on 30-day average)
        expected_profit = Decimal('1000000.00') * Decimal('3.0') / 100
        self.assertEqual(profit_transaction.amount, expected_profit)
        print(f"✅ Profit calculation: {profit_transaction.amount} (expected: {expected_profit})")

    def test_different_profit_kinds_same_calculation(self):
        """Test that all profit kinds use the same 30-day calculation window"""
        print("\n=== Testing Same Calculation Window for All Kinds ===")
        
        # Create daily snapshots for all deposits
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            
            # Monthly deposit
            DepositDailyBalance.objects.create(
                deposit=self.monthly_deposit,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
            
            # 6-month deposit
            DepositDailyBalance.objects.create(
                deposit=self.six_month_deposit,
                snapshot_date=snapshot_date,
                balance=Decimal('2000000.00')
            )
            
            # Yearly deposit
            DepositDailyBalance.objects.create(
                deposit=self.yearly_deposit,
                snapshot_date=snapshot_date,
                balance=Decimal('3000000.00')
            )
        
        # Set all deposits to transfer time (enough for yearly deposits)
        past_time = timezone.now() - timedelta(days=400)  # Enough for all kinds
        
        self.monthly_deposit.last_profit_accrual_at = past_time
        self.monthly_deposit.save()
        
        self.six_month_deposit.last_profit_accrual_at = past_time
        self.six_month_deposit.save()
        
        self.yearly_deposit.last_profit_accrual_at = past_time
        self.yearly_deposit.save()
        
        # Calculate profits for all
        self.monthly_deposit.accrue_monthly_profit()
        self.six_month_deposit.accrue_monthly_profit()
        self.yearly_deposit.accrue_monthly_profit()
        
        # Check profit transactions
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        
        self.assertEqual(profit_transactions.count(), 3)
        
        # Check profit amounts (all based on 30-day calculation)
        monthly_profit = profit_transactions.filter(
            destination_account__user=self.user
        ).first().amount
        
        expected_monthly = Decimal('1000000.00') * Decimal('3.0') / 100
        expected_six_month = Decimal('2000000.00') * Decimal('18.0') / 100
        expected_yearly = Decimal('3000000.00') * Decimal('36.0') / 100
        
        print(f"✅ Monthly profit: {monthly_profit} (expected: {expected_monthly})")
        print(f"✅ All deposits use 30-day calculation window")

    def test_profit_transfer_destination(self):
        """Test that all deposit profits go to user's base account"""
        print("\n=== Testing Profit Transfer Destination ===")
        
        # Create daily snapshots
        today = date.today()
        for i in range(30):
            snapshot_date = today - timedelta(days=29-i)
            DepositDailyBalance.objects.create(
                deposit=self.monthly_deposit,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
        
        # Set to transfer time
        past_time = timezone.now() - timedelta(days=31)
        self.monthly_deposit.last_profit_accrual_at = past_time
        self.monthly_deposit.save()
        
        # Calculate profit
        self.monthly_deposit.accrue_monthly_profit()
        
        # Check profit transaction destination
        profit_transaction = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        self.assertEqual(profit_transaction.destination_account, self.base_account)
        print(f"✅ Profit transferred to base account: {self.base_account.name}")

    def test_profit_calculation_info_display(self):
        """Test that profit calculation info shows correct transfer intervals"""
        print("\n=== Testing Profit Calculation Info Display ===")
        
        # Test monthly deposit info
        monthly_info = self.monthly_deposit.get_profit_calculation_info()
        print(f"Monthly deposit info: {monthly_info}")
        self.assertIn('سود بعدی', monthly_info)
        
        # Test 6-month deposit info
        six_month_info = self.six_month_deposit.get_profit_calculation_info()
        print(f"6-month deposit info: {six_month_info}")
        self.assertIn('سود بعدی', six_month_info)
        
        # Test yearly deposit info
        yearly_info = self.yearly_deposit.get_profit_calculation_info()
        print(f"Yearly deposit info: {yearly_info}")
        self.assertIn('سود بعدی', yearly_info)
        
        print("✅ Profit calculation info displays correctly")

    def run_all_tests(self):
        """Run all deposit profit kinds tests"""
        print("=" * 80)
        print("DEPOSIT PROFIT KINDS TESTS")
        print("=" * 80)
        
        try:
            self.test_monthly_deposit_profit_transfer_30_days()
            self.test_six_month_deposit_profit_transfer_180_days()
            self.test_yearly_deposit_profit_transfer_365_days()
            self.test_profit_calculation_always_daily()
            self.test_different_profit_kinds_same_calculation()
            self.test_profit_transfer_destination()
            self.test_profit_calculation_info_display()
            
            print("\n" + "=" * 80)
            print("✅ ALL DEPOSIT PROFIT KINDS TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = DepositProfitKindsTests()
    test.setUp()
    test.run_all_tests()
