"""
API Integration Tests

This module tests API integration functionality including:
- Transaction API creation
- Account API retrieval
- Deposit API creation
- User API retrieval
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from finance.models import User, Account, Deposit, Transaction
from finance.tests.test_config import FinanceTestCase


class APIIntegrationTests(FinanceTestCase, APITestCase):
    """Test API integration functionality"""
    
    def setUp(self):
        """Set up test data for API integration testing"""
        self.user = self.create_test_user('api_integration_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
    
    def test_transaction_api_creation(self):
        """Test transaction API creation"""
        url = reverse('transaction-list')
        data = {
            'source_account': self.rial_account.id,
            'destination_account': self.usd_account.id,
            'amount': '100000.00',
            'kind': Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            'exchange_rate': '50000.00'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['amount'], '100000.00')
    
    def test_account_api_retrieval(self):
        """Test account API retrieval"""
        url = reverse('account-detail', kwargs={'pk': self.rial_account.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Rial Account')
        self.assertEqual(response.data['account_type'], Account.ACCOUNT_TYPE_RIAL)
    
    def test_deposit_api_creation(self):
        """Test deposit API creation"""
        url = reverse('deposit-list')
        data = {
            'initial_balance': '500000.00',
            'monthly_profit_rate': '3.0',
            'profit_kind': Deposit.PROFIT_KIND_MONTHLY,
            'breakage_coefficient': '50.0'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['initial_balance'], '500000.00')
    
    def test_user_api_retrieval(self):
        """Test user API retrieval"""
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'api_integration_user')
        self.assertIn('accounts', response.data)
        self.assertIn('deposits', response.data)
