"""
Transaction Forms Tests

This module tests transaction form functionality including:
- Form initialization and validation
- Data handling and filtering
- Cross-currency validation
- Account filtering
"""

from decimal import Decimal
from django.test import TestCase
from finance.models import User, Account
from finance.forms.transaction_forms import TransactionAdminForm
from finance.forms.specialized_forms import WithdrawalRequestForm, CreditIncreaseForm, AccountTransferForm
from finance.tests.test_config import FinanceTestCase


class TransactionFormsTests(FinanceTestCase):
    """Test transaction forms functionality"""
    
    def setUp(self):
        """Set up test data for transaction forms testing"""
        self.user = self.create_test_user('transaction_forms_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
    
    def test_withdrawal_request_form_initialization(self):
        """Test withdrawal request form initialization"""
        form = WithdrawalRequestForm()
        self.assertIsNotNone(form)
    
    def test_withdrawal_request_form_with_data(self):
        """Test withdrawal request form with data"""
        form_data = {
            'source_account': self.rial_account.id,
            'amount': '100000.00',
            'withdrawal_card_number': '1234567890123456'
        }
        form = WithdrawalRequestForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_withdrawal_request_form_credit_increase_filtering(self):
        """Test withdrawal request form credit increase filtering"""
        form = WithdrawalRequestForm(user=self.user)
        # Should not include credit increase accounts
        account_choices = [choice[0] for choice in form.fields['source_account'].choices]
        self.assertNotIn('', account_choices)  # Empty choice should not be present
    
    def test_withdrawal_request_form_withdrawal_request_filtering(self):
        """Test withdrawal request form withdrawal request filtering"""
        form = WithdrawalRequestForm(user=self.user)
        # Should include withdrawal request accounts
        account_choices = [choice[0] for choice in form.fields['source_account'].choices]
        self.assertIn(self.rial_account.id, account_choices)
    
    def test_withdrawal_request_form_cross_currency_validation(self):
        """Test withdrawal request form cross-currency validation"""
        form_data = {
            'source_account': self.usd_account.id,  # USD account
            'amount': '100.00',
            'withdrawal_card_number': '1234567890123456'
        }
        form = WithdrawalRequestForm(data=form_data, user=self.user)
        # Should be valid for cross-currency
        self.assertTrue(form.is_valid())
    
    def test_withdrawal_request_form_cross_currency_with_exchange_rate(self):
        """Test withdrawal request form cross-currency with exchange rate"""
        form_data = {
            'source_account': self.usd_account.id,  # USD account
            'amount': '100.00',
            'withdrawal_card_number': '1234567890123456',
            'exchange_rate': '50000.00'  # Exchange rate
        }
        form = WithdrawalRequestForm(data=form_data, user=self.user)
        # Should be valid with exchange rate
        self.assertTrue(form.is_valid())
    
    def test_credit_increase_form_initialization(self):
        """Test credit increase form initialization"""
        form = CreditIncreaseForm(user=self.user)
        self.assertIsNotNone(form)
        self.assertEqual(form.user, self.user)
    
    def test_credit_increase_form_with_valid_data(self):
        """Test credit increase form with valid data"""
        form_data = {
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'comment': 'Test credit increase'
        }
        form = CreditIncreaseForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_credit_increase_form_account_filtering(self):
        """Test credit increase form account filtering"""
        form = CreditIncreaseForm(user=self.user)
        # Should include credit increase accounts
        account_choices = [choice[0] for choice in form.fields['destination_account'].choices]
        self.assertIn(self.rial_account.id, account_choices)
    
    def test_credit_increase_form_save(self):
        """Test credit increase form save"""
        form_data = {
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'comment': 'Test credit increase'
        }
        form = CreditIncreaseForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.destination_account, self.rial_account)
        self.assertEqual(transaction.amount, Decimal('100000.00'))
    
    def test_account_transfer_form_initialization(self):
        """Test account transfer form initialization"""
        form = AccountTransferForm(user=self.user)
        self.assertIsNotNone(form)
        self.assertEqual(form.user, self.user)
    
    def test_account_transfer_form_with_valid_data(self):
        """Test account transfer form with valid data"""
        form_data = {
            'source_account': self.rial_account.id,
            'destination_account': self.usd_account.id,
            'amount': '100000.00',
            'exchange_rate': '50000.00'
        }
        form = AccountTransferForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
    
    def test_account_transfer_form_account_filtering(self):
        """Test account transfer form account filtering"""
        form = AccountTransferForm(user=self.user)
        # Should include transfer accounts
        source_choices = [choice[0] for choice in form.fields['source_account'].choices]
        dest_choices = [choice[0] for choice in form.fields['destination_account'].choices]
        self.assertIn(self.rial_account.id, source_choices)
        self.assertIn(self.usd_account.id, dest_choices)
    
    def test_account_transfer_form_cross_currency_validation(self):
        """Test account transfer form cross-currency validation"""
        form_data = {
            'source_account': self.rial_account.id,
            'destination_account': self.usd_account.id,
            'amount': '100000.00',
            'exchange_rate': '50000.00'
        }
        form = AccountTransferForm(data=form_data, user=self.user)
        # Should be valid for cross-currency
        self.assertTrue(form.is_valid())
    
    def test_account_transfer_form_same_currency_no_exchange_rate(self):
        """Test account transfer form same currency no exchange rate"""
        form_data = {
            'source_account': self.rial_account.id,
            'destination_account': self.rial_account.id,  # Same currency
            'amount': '100000.00'
            # No exchange rate needed for same currency
        }
        form = AccountTransferForm(data=form_data, user=self.user)
        # Should be valid for same currency
        self.assertTrue(form.is_valid())
    
    def test_account_transfer_form_save(self):
        """Test account transfer form save"""
        form_data = {
            'source_account': self.rial_account.id,
            'destination_account': self.usd_account.id,
            'amount': '100000.00',
            'exchange_rate': '50000.00'
        }
        form = AccountTransferForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.source_account, self.rial_account)
        self.assertEqual(transaction.destination_account, self.usd_account)
        self.assertEqual(transaction.amount, Decimal('100000.00'))
        self.assertEqual(transaction.exchange_rate, Decimal('50000.00'))
