"""
User Serializer Tests

This module tests user serializer functionality including:
- Serializer creation and validation
- Relationships (accounts, deposits)
- Short user ID handling
- Validation errors
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account, Deposit
from finance.serializers import UserSerializer
from finance.tests.test_config import FinanceTestCase


class UserSerializerTests(FinanceTestCase):
    """Test user serializer functionality"""
    
    def setUp(self):
        """Set up test data for user serializer testing"""
        self.user = self.create_test_user('user_serializer_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('500000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
    
    def test_user_serializer_creation(self):
        """Test user serializer creation"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'card_number': '1234567890123456',
            'sheba_number': 'IR1234567890123456789012'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
    
    def test_user_serializer_accounts_relationship(self):
        """Test user serializer accounts relationship"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        # Check that accounts are included
        self.assertIn('accounts', data)
        self.assertEqual(len(data['accounts']), 1)
        self.assertEqual(data['accounts'][0]['name'], 'Test Rial Account')
    
    def test_user_serializer_deposits_relationship(self):
        """Test user serializer deposits relationship"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        # Check that deposits are included
        self.assertIn('deposits', data)
        self.assertEqual(len(data['deposits']), 1)
        self.assertEqual(data['deposits'][0]['initial_balance'], '500000.00')
    
    def test_user_serializer_short_user_id(self):
        """Test user serializer short user ID"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        # Check that short_user_id is included
        self.assertIn('short_user_id', data)
        self.assertEqual(data['short_user_id'], self.user.short_user_id)
    
    def test_user_serializer_validation_errors(self):
        """Test user serializer validation errors"""
        data = {
            'username': '',  # Empty username
            'email': 'invalid_email',  # Invalid email
            'first_name': '',  # Empty first name
            'last_name': '',  # Empty last name
            'card_number': '123',  # Invalid card number length
            'sheba_number': '123'  # Invalid SHEBA number length
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('email', serializer.errors)
        self.assertIn('card_number', serializer.errors)
        self.assertIn('sheba_number', serializer.errors)
