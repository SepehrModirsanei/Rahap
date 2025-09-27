"""
Account Serializer Tests

This module tests account serializer functionality including:
- Serializer creation and validation
- Balance calculation
- Validation errors
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account, Transaction
from finance.serializers import AccountSerializer
from finance.tests.test_config import FinanceTestCase


class AccountSerializerTests(FinanceTestCase):
    """Test account serializer functionality"""
    
    def setUp(self):
        """Set up test data for account serializer testing"""
        self.user = self.create_test_user('account_serializer_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
    
    def test_account_serializer_creation(self):
        """Test account serializer creation"""
        data = {
            'name': 'Test Account',
            'account_type': Account.ACCOUNT_TYPE_RIAL,
            'initial_balance': '1000000.00',
            'monthly_profit_rate': '3.0'
        }
        serializer = AccountSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        account = serializer.save(user=self.user)
        self.assertIsNotNone(account)
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.name, 'Test Account')
        self.assertEqual(account.account_type, Account.ACCOUNT_TYPE_RIAL)
        self.assertEqual(account.initial_balance, Decimal('1000000.00'))
    
    def test_account_serializer_balance_calculation(self):
        """Test account serializer balance calculation"""
        # Create a transaction that affects the account balance
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            applied=True
        )
        
        serializer = AccountSerializer(instance=self.rial_account)
        data = serializer.data
        
        # Check that balance is calculated correctly
        expected_balance = Decimal('1000000.00') - Decimal('100000.00')
        self.assertEqual(Decimal(data['balance']), expected_balance)
    
    def test_account_serializer_validation_errors(self):
        """Test account serializer validation errors"""
        data = {
            'name': '',  # Empty name
            'account_type': 'invalid_type',  # Invalid account type
            'initial_balance': '-1000000.00',  # Negative balance
            'monthly_profit_rate': '-3.0'  # Negative profit rate
        }
        serializer = AccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('account_type', serializer.errors)
