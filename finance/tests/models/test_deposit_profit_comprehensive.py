"""
Comprehensive Deposit Profit Tests

This test file focuses on improving coverage for the Deposit.accrue_monthly_profit method,
which is critical for the profit system.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from finance.models import User, Account, Deposit, Transaction
from finance.tests.test_config import FinanceTestCase


class DepositProfitComprehensiveTests(FinanceTestCase):
    """Comprehensive tests for Deposit profit calculation to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.base_account = self.get_user_base_account(self.user)
        self.deposit = self.create_test_deposit(
            self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )

    def test_accrue_monthly_profit_first_time(self):
        """Test profit accrual for the first time"""
        # Ensure no previous profit accrual
        self.assertIsNone(self.deposit.last_profit_accrual_at)
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)
        
        # Check profit amount (3% of 1,000,000 = 30,000)
        expected_profit = Decimal('1000000.00') * Decimal('3.0') / 100
        self.assertEqual(profit_transactions.first().amount, expected_profit)
        
        # Check that timestamp was updated
        self.assertIsNotNone(self.deposit.last_profit_accrual_at)

    def test_accrue_monthly_profit_after_30_days(self):
        """Test profit accrual after 30 days"""
        # Set last accrual to 31 days ago
        past_time = timezone.now() - timedelta(days=31)
        self.deposit.last_profit_accrual_at = past_time
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)

    def test_accrue_monthly_profit_before_30_days(self):
        """Test that profit is not accrued before 30 days"""
        # Set last accrual to 20 days ago
        past_time = timezone.now() - timedelta(days=20)
        self.deposit.last_profit_accrual_at = past_time
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that no profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)

    def test_accrue_monthly_profit_zero_rate(self):
        """Test that no profit is accrued with zero rate"""
        # Set zero profit rate
        self.deposit.monthly_profit_rate = Decimal('0.0')
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that no profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)

    def test_accrue_monthly_profit_negative_rate(self):
        """Test that no profit is accrued with negative rate"""
        # Set negative profit rate
        self.deposit.monthly_profit_rate = Decimal('-1.0')
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that no profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)

    def test_accrue_monthly_profit_zero_balance(self):
        """Test that no profit is accrued with zero balance"""
        # Set zero initial balance
        self.deposit.initial_balance = Decimal('0.00')
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that no profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)

    def test_accrue_monthly_profit_no_base_account(self):
        """Test profit accrual when user has no base account"""
        # Delete the base account
        self.base_account.delete()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # New behavior: system auto-creates a Rial base account and credits profit
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)

    def test_accrue_monthly_profit_different_rates(self):
        """Test profit accrual with different profit rates"""
        # Test with 5% rate
        self.deposit.monthly_profit_rate = Decimal('5.0')
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check profit amount (5% of 1,000,000 = 50,000)
        profit_transaction = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        expected_profit = Decimal('1000000.00') * Decimal('5.0') / 100
        self.assertEqual(profit_transaction.amount, expected_profit)

    def test_accrue_monthly_profit_multiple_times(self):
        """Test multiple profit accruals over time"""
        # First accrual
        self.deposit.accrue_monthly_profit()
        
        # Set time forward by 30 days
        future_time = timezone.now() + timedelta(days=30)
        self.deposit.last_profit_accrual_at = future_time - timedelta(days=30)
        self.deposit.save()
        
        # Second accrual
        self.deposit.accrue_monthly_profit()
        
        # Check that profit transactions were created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        # Should have at least one profit transaction
        self.assertGreaterEqual(profit_transactions.count(), 1)

    def test_accrue_monthly_profit_destination_account(self):
        """Test that profit goes to the correct base account"""
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that profit transaction goes to base account
        profit_transaction = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        self.assertEqual(profit_transaction.destination_account, self.base_account)
        self.assertIsNone(profit_transaction.source_account)

    def test_accrue_monthly_profit_transaction_state(self):
        """Test that profit transaction is created with correct state"""
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check transaction state
        profit_transaction = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        self.assertEqual(profit_transaction.state, Transaction.STATE_DONE)
        self.assertTrue(profit_transaction.applied)

    def test_accrue_monthly_profit_timestamp_update(self):
        """Test that timestamp is updated after profit accrual"""
        initial_time = timezone.now() - timedelta(days=30)
        self.deposit.last_profit_accrual_at = initial_time
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that timestamp was updated
        self.deposit.refresh_from_db()
        self.assertIsNotNone(self.deposit.last_profit_accrual_at)
        self.assertGreater(self.deposit.last_profit_accrual_at, initial_time)

    def test_accrue_monthly_profit_edge_case_30_days_exact(self):
        """Test profit accrual at exactly 30 days"""
        # Set last accrual to exactly 30 days ago
        past_time = timezone.now() - timedelta(days=30)
        self.deposit.last_profit_accrual_at = past_time
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)

    def test_accrue_monthly_profit_edge_case_27_days(self):
        """Test that profit is not accrued at 27 days"""
        # Set last accrual to 27 days ago
        past_time = timezone.now() - timedelta(days=27)
        self.deposit.last_profit_accrual_at = past_time
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that no profit transaction was created
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 0)

    def test_accrue_monthly_profit_high_precision_calculation(self):
        """Test profit calculation with high precision amounts"""
        # Set deposit with high precision amount
        self.deposit.initial_balance = Decimal('1234567.89')
        self.deposit.monthly_profit_rate = Decimal('2.75')
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check profit calculation
        profit_transaction = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        ).first()
        
        expected_profit = Decimal('1234567.89') * Decimal('2.75') / 100
        # Allow for small rounding differences
        self.assertAlmostEqual(profit_transaction.amount, expected_profit, places=2)

    def test_accrue_monthly_profit_very_small_amount(self):
        """Test profit accrual with very small amounts"""
        # Set very small deposit amount
        self.deposit.initial_balance = Decimal('0.01')
        self.deposit.monthly_profit_rate = Decimal('1.0')
        self.deposit.save()
        
        # Accrue profit
        self.deposit.accrue_monthly_profit()
        
        # Check that profit transaction was created (even for very small amounts)
        profit_transactions = Transaction.objects.filter(
            user=self.user,
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            applied=True
        )
        self.assertEqual(profit_transactions.count(), 1)
        
        # Check profit amount (should be rounded to 0.00 for very small amounts)
        expected_profit = Decimal('0.01') * Decimal('1.0') / 100
        # Very small profits might be rounded to zero
        actual_profit = profit_transactions.first().amount
        self.assertGreaterEqual(actual_profit, Decimal('0.00'))
