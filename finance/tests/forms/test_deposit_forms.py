"""
Deposit Forms Tests

This module tests deposit form functionality including:
- Form initialization and validation
- Data handling and filtering
- Account filtering
- Form save functionality
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account
from finance.forms.specialized_forms import DepositTransactionForm
from finance.tests.test_config import FinanceTestCase


class DepositFormsTests(FinanceTestCase):
    """Test deposit forms functionality"""
    
    def setUp(self):
        """Set up test data for deposit forms testing"""
        self.user = self.create_test_user('deposit_forms_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
    
    def test_deposit_transaction_form_initialization(self):
        """Test deposit transaction form initialization"""
        form = DepositTransactionForm(user=self.user)
        self.assertIsNotNone(form)
        self.assertEqual(form.user, self.user)
    
    def test_deposit_transaction_form_with_valid_data(self):
        """Test deposit transaction form with valid data"""
        form_data = {
            'source_account': self.rial_account.id,
            'amount': '100000.00',
            'comment': 'Test deposit transaction'
        }
        form = DepositTransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_deposit_transaction_form_account_filtering(self):
        """Test deposit transaction form account filtering"""
        form = DepositTransactionForm(user=self.user)
        # Should include deposit transaction accounts
        account_choices = [choice[0] for choice in form.fields['source_account'].choices]
        self.assertIn(self.rial_account.id, account_choices)
    
    def test_deposit_transaction_form_save(self):
        """Test deposit transaction form save"""
        form_data = {
            'source_account': self.rial_account.id,
            'amount': '100000.00',
            'comment': 'Test deposit transaction'
        }
        form = DepositTransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.source_account, self.rial_account)
        self.assertEqual(transaction.amount, Decimal('100000.00'))
