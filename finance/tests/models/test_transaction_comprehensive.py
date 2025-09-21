"""
Comprehensive Transaction Model Tests

This test file focuses on improving coverage for the Transaction model,
which is the core of the financial system.
"""

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
from finance.models import User, Account, Deposit, Transaction
from finance.tests.test_config import FinanceTestCase


class TransactionComprehensiveTests(FinanceTestCase):
    """Comprehensive tests for Transaction model to improve coverage"""
    
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
        self.deposit = self.create_test_deposit(
            self.user,
            initial_balance=Decimal('500000.00'),
            monthly_profit_rate=Decimal('3.0')
        )

    def test_transaction_creation_with_code(self):
        """Test transaction creation with automatic code generation"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        self.assertIsNotNone(transaction.transaction_code)
        self.assertTrue(len(transaction.transaction_code) > 0)
        self.assertEqual(transaction.kind, Transaction.KIND_CREDIT_INCREASE)
        self.assertEqual(transaction.amount, Decimal('100000.00'))

    def test_credit_increase_application(self):
        """Test credit increase transaction application"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('200000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        # Apply the transaction
        transaction.apply()
        
        # Verify transaction is marked as applied
        self.assertTrue(transaction.applied)
        
        # Verify account balance increased
        self.assertEqual(self.rial_account.balance, Decimal('1200000.00'))

    def test_withdrawal_request_application(self):
        """Test withdrawal request transaction application"""
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE,
            withdrawal_card_number='1234567890123456'
        )
        
        # Apply the transaction
        transaction.apply()
        
        # Verify transaction is marked as applied
        self.assertTrue(transaction.applied)

    def test_account_to_deposit_initial_application(self):
        """Test account to deposit initial transaction application"""
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_deposit=self.deposit,
            amount=Decimal('300000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
            state=Transaction.STATE_DONE
        )
        
        # Apply the transaction
        transaction.apply()
        
        # Verify transaction is marked as applied
        self.assertTrue(transaction.applied)

    def test_profit_account_application(self):
        """Test profit account transaction application"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('25000.00'),
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        
        # Apply the transaction
        transaction.apply()
        
        # Verify transaction is marked as applied
        self.assertTrue(transaction.applied)

    def test_profit_deposit_to_account_application(self):
        """Test profit deposit to account transaction application"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('15000.00'),
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        
        # Apply the transaction
        transaction.apply()
        
        # Verify transaction is marked as applied
        self.assertTrue(transaction.applied)

    def test_transaction_apply_already_applied(self):
        """Test that already applied transactions are not applied again"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Try to apply again
        transaction.apply()
        
        # Should remain applied (no change)
        self.assertTrue(transaction.applied)

    def test_transaction_apply_future_scheduled(self):
        """Test that future scheduled transactions are not applied"""
        future_time = timezone.now() + timedelta(days=1)
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE,
            scheduled_for=future_time
        )
        
        # Try to apply
        transaction.apply()
        
        # Should not be applied
        self.assertFalse(transaction.applied)

    def test_transaction_apply_not_done_state(self):
        """Test that transactions not in DONE state are not applied"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_WAITING_TREASURY
        )
        
        # Try to apply
        transaction.apply()
        
        # Should not be applied
        self.assertFalse(transaction.applied)

    def test_transaction_apply_missing_destination_account(self):
        """Test that credit increase without destination account is not applied"""
        # This should raise ValidationError during creation due to auto-apply
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_CREDIT_INCREASE,
                state=Transaction.STATE_DONE  # Done state to trigger validation
            )

    def test_transaction_apply_missing_source_account(self):
        """Test that withdrawal request without source account is not applied"""
        # This should raise ValidationError during creation due to auto-apply
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_WITHDRAWAL_REQUEST,
                state=Transaction.STATE_DONE  # Done state to trigger validation
            )

    def test_transaction_advance_state_waiting_treasury_to_waiting_sandogh(self):
        """Test state advancement from WAITING_TREASURY to WAITING_SANDOGH"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_WAITING_TREASURY
        )
        
        # Advance state
        result = transaction.advance_state()
        
        # Should advance to WAITING_SANDOGH
        self.assertTrue(result)
        self.assertEqual(transaction.state, Transaction.STATE_WAITING_SANDOGH)

    def test_transaction_advance_state_verified_khazanedar_to_done(self):
        """Test state advancement from VERIFIED_KHAZANEDAR to DONE"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_VERIFIED_KHAZANEDAR
        )
        
        # Advance state
        result = transaction.advance_state()
        
        # Should advance to DONE
        self.assertTrue(result)
        self.assertEqual(transaction.state, Transaction.STATE_DONE)

    def test_transaction_advance_state_done_no_change(self):
        """Test that DONE state transactions don't advance"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        # Try to advance state
        result = transaction.advance_state()
        
        # Should not advance
        self.assertFalse(result)
        self.assertEqual(transaction.state, Transaction.STATE_DONE)

    def test_transaction_advance_state_waiting_sandogh_to_verified(self):
        """Test that WAITING_SANDOGH state transactions advance to VERIFIED_KHAZANEDAR"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_WAITING_SANDOGH
        )
        
        # Try to advance state
        result = transaction.advance_state()
        
        # Should advance to VERIFIED_KHAZANEDAR
        self.assertTrue(result)
        self.assertEqual(transaction.state, Transaction.STATE_VERIFIED_KHAZANEDAR)

    def test_transaction_clean_validation(self):
        """Test transaction clean method validation"""
        # Test valid transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Should not raise validation error
        transaction.clean()

    def test_transaction_str_representation(self):
        """Test transaction string representation"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        str_repr = str(transaction)
        self.assertIn('credit_increase', str_repr)
        self.assertIn('100000.00', str_repr)

    def test_transaction_meta_verbose_names(self):
        """Test transaction model meta verbose names"""
        self.assertEqual(Transaction._meta.verbose_name, 'تراکنش')
        self.assertEqual(Transaction._meta.verbose_name_plural, 'تراکنش‌ها')
