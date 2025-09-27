"""
Deposit Balance Calculation Tests

This module tests deposit balance calculation functionality including:
- Balance calculation with transactions
- Balance calculation without transactions
- Multiple transaction scenarios
- Edge cases and boundary conditions
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account, Deposit, Transaction
from finance.tests.test_config import FinanceTestCase


class DepositBalanceTests(FinanceTestCase):
    """Test deposit balance calculation functionality"""
    
    def setUp(self):
        """Set up test data for deposit balance testing"""
        self.user = self.create_test_user('deposit_balance_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
    
    def test_deposit_balance_calculation_with_transactions(self):
        """Test deposit balance calculation with transactions"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Create a transaction that adds money to the deposit
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_deposit=deposit,
            amount=Decimal('500000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
            applied=True
        )
        
        # Check balance calculation
        expected_balance = Decimal('1000000.00') + Decimal('500000.00')
        self.assertEqual(deposit.balance, expected_balance)
    
    def test_deposit_balance_calculation_without_transactions(self):
        """Test deposit balance calculation without transactions"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Check balance calculation (should be initial balance)
        self.assertEqual(deposit.balance, Decimal('1000000.00'))
    
    def test_deposit_balance_calculation_multiple_transactions(self):
        """Test deposit balance calculation with multiple transactions"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Create multiple transactions
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_deposit=deposit,
            amount=Decimal('500000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
            applied=True
        )
        
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_deposit=deposit,
            amount=Decimal('300000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
            applied=True
        )
        
        # Check balance calculation
        expected_balance = Decimal('1000000.00') + Decimal('500000.00') + Decimal('300000.00')
        self.assertEqual(deposit.balance, expected_balance)
