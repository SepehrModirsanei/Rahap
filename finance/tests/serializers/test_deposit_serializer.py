"""
Deposit Serializer Tests

This module tests deposit serializer functionality including:
- Serializer creation and validation
- Balance calculation
- Profit calculation info
- Validation errors
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account, Deposit, Transaction
from finance.serializers import DepositSerializer
from finance.tests.test_config import FinanceTestCase


class DepositSerializerTests(FinanceTestCase):
    """Test deposit serializer functionality"""
    
    def setUp(self):
        """Set up test data for deposit serializer testing"""
        self.user = self.create_test_user('deposit_serializer_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
    
    def test_deposit_serializer_creation(self):
        """Test deposit serializer creation"""
        data = {
            'initial_balance': '1000000.00',
            'monthly_profit_rate': '3.0',
            'profit_kind': Deposit.PROFIT_KIND_MONTHLY,
            'breakage_coefficient': '50.0'
        }
        serializer = DepositSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        deposit = serializer.save(user=self.user)
        self.assertIsNotNone(deposit)
        self.assertEqual(deposit.user, self.user)
        self.assertEqual(deposit.initial_balance, Decimal('1000000.00'))
        self.assertEqual(deposit.monthly_profit_rate, Decimal('3.0'))
    
    def test_deposit_serializer_balance_calculation(self):
        """Test deposit serializer balance calculation"""
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
        
        serializer = DepositSerializer(instance=deposit)
        data = serializer.data
        
        # Check that balance is calculated correctly
        expected_balance = Decimal('1000000.00') + Decimal('500000.00')
        self.assertEqual(Decimal(data['balance']), expected_balance)
    
    def test_deposit_serializer_profit_calculation_info(self):
        """Test deposit serializer profit calculation info"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        serializer = DepositSerializer(instance=deposit)
        data = serializer.data
        
        # Check that profit calculation info is included
        self.assertIn('profit_calculation_info', data)
        profit_info = data['profit_calculation_info']
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_serializer_validation_errors(self):
        """Test deposit serializer validation errors"""
        data = {
            'initial_balance': '-1000000.00',  # Negative balance
            'monthly_profit_rate': '-3.0',    # Negative profit rate
            'profit_kind': 'invalid_kind',     # Invalid profit kind
            'breakage_coefficient': '150.0'   # Over 100%
        }
        serializer = DepositSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('initial_balance', serializer.errors)
        self.assertIn('monthly_profit_rate', serializer.errors)
        self.assertIn('profit_kind', serializer.errors)
        self.assertIn('breakage_coefficient', serializer.errors)
