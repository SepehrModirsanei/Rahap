"""
Transaction Serializer Tests

This module tests transaction serializer functionality including:
- Serializer creation and validation
- Bank destination handling
- Saved bank info functionality
- Validation errors and read-only fields
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account, Transaction
from finance.serializers import TransactionSerializer
from finance.tests.test_config import FinanceTestCase


class TransactionSerializerTests(FinanceTestCase):
    """Test transaction serializer functionality"""
    
    def setUp(self):
        """Set up test data for transaction serializer testing"""
        self.user = self.create_test_user('transaction_serializer_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
    
    def test_transaction_serializer_creation(self):
        """Test transaction serializer creation"""
        data = {
            'source_account': self.rial_account.id,
            'destination_account': self.usd_account.id,
            'amount': '100000.00',
            'kind': Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            'exchange_rate': '50000.00'
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        transaction = serializer.save(user=self.user)
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.source_account, self.rial_account)
        self.assertEqual(transaction.destination_account, self.usd_account)
        self.assertEqual(transaction.amount, Decimal('100000.00'))
    
    def test_transaction_serializer_bank_destination_card(self):
        """Test transaction serializer with bank destination card"""
        data = {
            'source_account': self.rial_account.id,
            'amount': '100000.00',
            'kind': Transaction.KIND_WITHDRAWAL_REQUEST,
            'bank_destination': '1234567890123456'
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test that the serializer correctly maps bank_destination to withdrawal fields
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['withdrawal_card_number'], '1234567890123456')
        self.assertEqual(validated_data['withdrawal_sheba_number'], '')
    
    def test_transaction_serializer_bank_destination_sheba(self):
        """Test transaction serializer with bank destination SHEBA"""
        data = {
            'source_account': self.rial_account.id,
            'amount': '100000.00',
            'kind': Transaction.KIND_WITHDRAWAL_REQUEST,
            'bank_destination': 'IR1234567890123456789012'
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test that the serializer correctly maps bank_destination to withdrawal fields
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['withdrawal_sheba_number'], 'IR1234567890123456789012')
        self.assertEqual(validated_data['withdrawal_card_number'], '')
    
    def test_transaction_serializer_saved_bank_info(self):
        """Test transaction serializer with saved bank info"""
        # Set user bank info
        self.user.card_number = '1234567890123456'
        self.user.sheba_number = 'IR1234567890123456789012'
        
        serializer = TransactionSerializer(context={'request': type('obj', (object,), {'user': self.user})()})
        bank_info = serializer.get_saved_bank_info(None)
        
        self.assertIsNotNone(bank_info)
        self.assertIn('card_number', bank_info)
        self.assertIn('sheba_number', bank_info)
    
    def test_transaction_serializer_saved_bank_info_no_user(self):
        """Test transaction serializer with no user context"""
        serializer = TransactionSerializer()
        serializer._context = {}
        
        try:
            bank_info = serializer.get_saved_bank_info(None)
            # Should handle gracefully
            self.assertIsNone(bank_info)
        except AttributeError:
            # Expected when no user context
            pass
    
    def test_transaction_serializer_validation_errors(self):
        """Test transaction serializer validation errors"""
        data = {
            'source_account': self.rial_account.id,
            'amount': '-100000.00',  # Negative amount
            'kind': Transaction.KIND_ACCOUNT_TO_ACCOUNT
        }
        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_transaction_serializer_read_only_fields(self):
        """Test transaction serializer read-only fields"""
        data = {
            'source_account': self.rial_account.id,
            'destination_account': self.usd_account.id,
            'amount': '100000.00',
            'kind': Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            'transaction_code': 'TEST123',  # Read-only field
            'applied': True,  # Read-only field
            'created_at': '2024-01-01T00:00:00Z'  # Read-only field
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        transaction = serializer.save(user=self.user)
        # Read-only fields should not be set from data
        self.assertNotEqual(transaction.transaction_code, 'TEST123')
        self.assertFalse(transaction.applied)
        self.assertIsNotNone(transaction.created_at)
