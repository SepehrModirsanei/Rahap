"""
Comprehensive Forms Tests

This test file focuses on improving coverage for the forms module,
which contains transaction and specialized forms.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from decimal import Decimal
from finance.forms.transaction_forms import TransactionAdminForm
from finance.forms.specialized_forms import (
    WithdrawalRequestForm,
    CreditIncreaseForm,
    AccountTransferForm,
    ProfitTransactionForm,
    DepositTransactionForm
)
from finance.models import User, Account, Deposit, Transaction
from finance.tests.test_config import FinanceTestCase


class TransactionAdminFormTests(FinanceTestCase):
    """Tests for TransactionAdminForm to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.rial_account = self.create_test_account(
            self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )
        self.gold_account = self.create_test_account(
            self.user,
            name='Test Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('10.00')
        )

    def test_form_initialization(self):
        """Test form initialization"""
        form = TransactionAdminForm()
        self.assertIsInstance(form, TransactionAdminForm)
        self.assertIn('user', form.fields)
        self.assertIn('kind', form.fields)
        self.assertIn('amount', form.fields)

    def test_form_with_data(self):
        """Test form with valid data"""
        form_data = {
            'user': self.user.id,
            'kind': Transaction.KIND_CREDIT_INCREASE,
            'amount': '100000.00',
            'destination_account': self.rial_account.id,
            'state': Transaction.STATE_DONE
        }
        form = TransactionAdminForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_credit_increase_filtering(self):
        """Test account filtering for credit increase"""
        form_data = {
            'user': self.user.id,
            'kind': Transaction.KIND_CREDIT_INCREASE
        }
        form = TransactionAdminForm(data=form_data)
        form._filter_account_choices()
        
        # Should only show rial accounts for credit increase
        self.assertIn(self.rial_account, form.fields['destination_account'].queryset)
        self.assertNotIn(self.gold_account, form.fields['destination_account'].queryset)

    def test_form_withdrawal_request_filtering(self):
        """Test account filtering for withdrawal request"""
        form_data = {
            'user': self.user.id,
            'kind': Transaction.KIND_WITHDRAWAL_REQUEST
        }
        form = TransactionAdminForm(data=form_data)
        form._filter_account_choices()
        
        # Should only show rial accounts for withdrawal request
        self.assertIn(self.rial_account, form.fields['source_account'].queryset)
        self.assertNotIn(self.gold_account, form.fields['source_account'].queryset)

    def test_form_cross_currency_validation(self):
        """Test cross-currency validation"""
        form_data = {
            'user': self.user.id,
            'kind': Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            'source_account': self.rial_account.id,
            'destination_account': self.gold_account.id,
            'amount': '100000.00',
            'exchange_rate': '',  # Missing exchange rate
            'state': Transaction.STATE_DONE
        }
        form = TransactionAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('exchange_rate', form.errors)

    def test_form_cross_currency_with_exchange_rate(self):
        """Test cross-currency with valid exchange rate"""
        form_data = {
            'user': self.user.id,
            'kind': Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            'source_account': self.rial_account.id,
            'destination_account': self.gold_account.id,
            'amount': '100000.00',
            'exchange_rate': '0.0001',
            'state': Transaction.STATE_DONE
        }
        form = TransactionAdminForm(data=form_data)
        self.assertTrue(form.is_valid())


class WithdrawalRequestFormTests(FinanceTestCase):
    """Tests for WithdrawalRequestForm to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.rial_account = self.create_test_account(
            self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )

    def test_form_initialization(self):
        """Test form initialization"""
        form = WithdrawalRequestForm()
        self.assertIsInstance(form, WithdrawalRequestForm)
        self.assertEqual(form.instance.kind, Transaction.KIND_WITHDRAWAL_REQUEST)

    def test_form_with_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'amount': '100000.00',
            'state': Transaction.STATE_DONE,
            'withdrawal_card_number': '1234567890123456'
        }
        dummy_image = SimpleUploadedFile('receipt.jpg', b"filecontent", content_type='image/jpeg')
        form = WithdrawalRequestForm(data=form_data, files={'receipt': dummy_image})
        self.assertTrue(form.is_valid())

    def test_form_account_filtering(self):
        """Test account filtering for withdrawal request"""
        form_data = {
            'user': self.user.id
        }
        form = WithdrawalRequestForm(data=form_data)
        form._filter_account_choices()
        
        # Should only show rial accounts
        self.assertIn(self.rial_account, form.fields['source_account'].queryset)

    def test_form_save(self):
        """Test form save"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'amount': '100000.00',
            'state': Transaction.STATE_DONE,
            'withdrawal_card_number': '1234567890123456'
        }
        dummy_image = SimpleUploadedFile('receipt.jpg', b"filecontent", content_type='image/jpeg')
        form = WithdrawalRequestForm(data=form_data, files={'receipt': dummy_image})
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertEqual(transaction.kind, Transaction.KIND_WITHDRAWAL_REQUEST)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.source_account, self.rial_account)


class CreditIncreaseFormTests(FinanceTestCase):
    """Tests for CreditIncreaseForm to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.rial_account = self.create_test_account(
            self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )

    def test_form_initialization(self):
        """Test form initialization"""
        form = CreditIncreaseForm()
        self.assertIsInstance(form, CreditIncreaseForm)
        self.assertEqual(form.instance.kind, Transaction.KIND_CREDIT_INCREASE)

    def test_form_with_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'user': self.user.id,
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'state': Transaction.STATE_DONE
        }
        form = CreditIncreaseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_account_filtering(self):
        """Test account filtering for credit increase"""
        form_data = {
            'user': self.user.id
        }
        form = CreditIncreaseForm(data=form_data)
        form._filter_account_choices()
        
        # Should only show rial accounts
        self.assertIn(self.rial_account, form.fields['destination_account'].queryset)

    def test_form_save(self):
        """Test form save"""
        form_data = {
            'user': self.user.id,
            'destination_account': self.rial_account.id,
            'amount': '100000.00',
            'state': Transaction.STATE_DONE
        }
        form = CreditIncreaseForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertEqual(transaction.kind, Transaction.KIND_CREDIT_INCREASE)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.destination_account, self.rial_account)


class AccountTransferFormTests(FinanceTestCase):
    """Tests for AccountTransferForm to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.rial_account = self.create_test_account(
            self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )
        self.gold_account = self.create_test_account(
            self.user,
            name='Test Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('10.00')
        )

    def test_form_initialization(self):
        """Test form initialization"""
        form = AccountTransferForm()
        self.assertIsInstance(form, AccountTransferForm)
        self.assertEqual(form.instance.kind, Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT)

    def test_form_with_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'destination_account': self.gold_account.id,
            'amount': '100000.00',
            'exchange_rate': '0.0001',
            'state': Transaction.STATE_DONE
        }
        form = AccountTransferForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_account_filtering(self):
        """Test account filtering for transfer"""
        form_data = {
            'user': self.user.id
        }
        form = AccountTransferForm(data=form_data)
        form._filter_account_choices()
        
        # Should show all user accounts
        self.assertIn(self.rial_account, form.fields['source_account'].queryset)
        self.assertIn(self.gold_account, form.fields['destination_account'].queryset)

    def test_form_cross_currency_validation(self):
        """Test cross-currency validation"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'destination_account': self.gold_account.id,
            'amount': '100000.00',
            'exchange_rate': '',  # Missing exchange rate
            'state': Transaction.STATE_DONE
        }
        form = AccountTransferForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('exchange_rate', form.errors)

    def test_form_same_currency_no_exchange_rate(self):
        """Test same currency transfer without exchange rate"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'destination_account': self.rial_account.id,  # Same account type
            'amount': '100000.00',
            'exchange_rate': '',  # No exchange rate needed
            'state': Transaction.STATE_DONE
        }
        form = AccountTransferForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_save(self):
        """Test form save"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'destination_account': self.gold_account.id,
            'amount': '100000.00',
            'exchange_rate': '0.0001',
            'state': Transaction.STATE_DONE
        }
        form = AccountTransferForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertEqual(transaction.kind, Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.source_account, self.rial_account)
        self.assertEqual(transaction.destination_account, self.gold_account)


class ProfitTransactionFormTests(FinanceTestCase):
    """Tests for ProfitTransactionForm to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.rial_account = self.create_test_account(
            self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )

    def test_form_initialization(self):
        """Test form initialization"""
        form = ProfitTransactionForm()
        self.assertIsInstance(form, ProfitTransactionForm)
        self.assertEqual(form.instance.kind, Transaction.KIND_PROFIT_ACCOUNT)

    def test_form_with_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'user': self.user.id,
            'destination_account': self.rial_account.id,
            'amount': '25000.00',
            'state': Transaction.STATE_DONE
        }
        form = ProfitTransactionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_account_filtering(self):
        """Test account filtering for profit transaction"""
        form_data = {
            'user': self.user.id
        }
        form = ProfitTransactionForm(data=form_data)
        form._filter_account_choices()
        
        # Should show all user accounts
        self.assertIn(self.rial_account, form.fields['destination_account'].queryset)

    def test_form_save(self):
        """Test form save"""
        form_data = {
            'user': self.user.id,
            'destination_account': self.rial_account.id,
            'amount': '25000.00',
            'state': Transaction.STATE_DONE
        }
        form = ProfitTransactionForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertEqual(transaction.kind, Transaction.KIND_PROFIT_ACCOUNT)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.destination_account, self.rial_account)


class DepositTransactionFormTests(FinanceTestCase):
    """Tests for DepositTransactionForm to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.rial_account = self.create_test_account(
            self.user,
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )
        self.deposit = self.create_test_deposit(
            self.user,
            initial_balance=Decimal('500000.00'),
            monthly_profit_rate=Decimal('3.0')
        )

    def test_form_initialization(self):
        """Test form initialization"""
        form = DepositTransactionForm()
        self.assertIsInstance(form, DepositTransactionForm)
        self.assertEqual(form.instance.kind, Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL)

    def test_form_with_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'destination_deposit': self.deposit.id,
            'amount': '300000.00',
            'state': Transaction.STATE_DONE
        }
        form = DepositTransactionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_choices_filtering(self):
        """Test choices filtering for deposit transaction"""
        form_data = {
            'user': self.user.id
        }
        form = DepositTransactionForm(data=form_data)
        form._filter_choices()
        
        # Should show user accounts and deposits
        self.assertIn(self.rial_account, form.fields['source_account'].queryset)
        self.assertIn(self.deposit, form.fields['destination_deposit'].queryset)

    def test_form_save(self):
        """Test form save"""
        form_data = {
            'user': self.user.id,
            'source_account': self.rial_account.id,
            'destination_deposit': self.deposit.id,
            'amount': '300000.00',
            'state': Transaction.STATE_DONE
        }
        form = DepositTransactionForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        transaction = form.save()
        self.assertEqual(transaction.kind, Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.source_account, self.rial_account)
        self.assertEqual(transaction.destination_deposit, self.deposit)

    def test_form_no_user_selected(self):
        """Test form behavior when no user is selected"""
        form = DepositTransactionForm()
        form._filter_choices()
        
        # Should show no accounts or deposits
        self.assertEqual(form.fields['source_account'].queryset.count(), 0)
        self.assertEqual(form.fields['destination_deposit'].queryset.count(), 0)
