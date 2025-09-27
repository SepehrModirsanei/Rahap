"""
Specialized Forms Tests

This module tests specialized form functionality including:
- Form initialization and validation
- Data handling and filtering
- Choices filtering
- Form save functionality
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account, Transaction
from finance.forms.specialized_forms import ProfitTransactionForm, DepositTransactionForm
from finance.tests.test_config import FinanceTestCase


class SpecializedFormsTests(FinanceTestCase):
    """Test specialized forms functionality"""
    
    def setUp(self):
        """Set up test data for specialized forms testing"""
        self.user = self.create_test_user('specialized_forms_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
    
    def test_profit_transaction_form_initialization(self):
        """Test profit transaction form initialization"""
        form = ProfitTransactionForm(user=self.user)
        self.assertIsNotNone(form)
        self.assertEqual(form.user, self.user)
    
    def test_profit_transaction_form_with_valid_data(self):
        """Test profit transaction form with valid data"""
        form_data = {
            'user': self.user.id,
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'state': Transaction.STATE_DONE,
            'comment': 'Test profit transaction'
        }
        form = ProfitTransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_profit_transaction_form_choices_filtering(self):
        """Test profit transaction form choices filtering"""
        form_data = {'user': self.user.id}
        form = ProfitTransactionForm(data=form_data, user=self.user)
        # Should include profit transaction choices
        account_choices = [choice[0] for choice in form.fields['destination_account'].choices]
        self.assertIn(self.rial_account.id, account_choices)
    
    def test_profit_transaction_form_save(self):
        """Test profit transaction form save"""
        form_data = {
            'user': self.user.id,
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'state': Transaction.STATE_DONE,
            'comment': 'Test profit transaction'
        }
        form = ProfitTransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.destination_account, self.rial_account)
        self.assertEqual(transaction.amount, Decimal('100000.00'))
    
    def test_profit_transaction_form_no_user_selected(self):
        """Test profit transaction form with no user selected"""
        form_data = {
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'comment': 'Test profit transaction'
        }
        form = ProfitTransactionForm(data=form_data, user=None)
        # Should handle None user gracefully
        self.assertIsNotNone(form)
