"""
Comprehensive Transaction State Log Tests

This module tests the TransactionStateLog model functionality including:
- State log creation and validation
- Persian date formatting and display
- State transition tracking
- Admin interface integration
- Signal integration and automatic logging

Test Coverage:
- State log creation and field validation
- Persian date formatting methods
- State transition logging
- Admin display methods
- Signal integration testing
- Edge cases and error handling
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from finance.models import User, Account, Transaction, TransactionStateLog
from finance.tests.test_config import FinanceTestCase


class TransactionStateLogComprehensiveTests(FinanceTestCase):
    """Test comprehensive transaction state log functionality"""
    
    def setUp(self):
        """Set up test data for state log testing"""
        self.user = self.create_test_user('statelog_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456'
        )
    
    def test_state_log_creation(self):
        """Test basic state log creation"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user,
            notes='Finance manager approved the transaction'
        )
        
        self.assertEqual(state_log.transaction, self.transaction)
        self.assertEqual(state_log.from_state, Transaction.STATE_WAITING_FINANCE_MANAGER)
        self.assertEqual(state_log.to_state, Transaction.STATE_WAITING_TREASURY)
        self.assertEqual(state_log.changed_by, self.user)
        self.assertEqual(state_log.notes, 'Finance manager approved the transaction')
    
    def test_state_log_automatic_timestamps(self):
        """Test that state log timestamps are set automatically"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Check that timestamps are set
        self.assertIsNotNone(state_log.created_at)
        self.assertIsNotNone(state_log.changed_at)
        
        # Check that changed_at is close to now
        now = timezone.now()
        time_diff = abs((now - state_log.changed_at).total_seconds())
        self.assertLess(time_diff, 5)  # Within 5 seconds
    
    def test_state_log_persian_date_display(self):
        """Test Persian date display methods"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Test Persian date display
        persian_created = state_log.get_persian_created_at()
        persian_changed = state_log.get_persian_changed_at()
        
        self.assertIsNotNone(persian_created)
        self.assertIsNotNone(persian_changed)
        
        # Check that Persian dates are strings
        self.assertIsInstance(persian_created, str)
        self.assertIsInstance(persian_changed, str)
        
        # Check that Persian dates contain Persian characters
        self.assertTrue(any('\u0600' <= char <= '\u06FF' for char in persian_created))
        self.assertTrue(any('\u0600' <= char <= '\u06FF' for char in persian_changed))
    
    def test_state_log_state_display_methods(self):
        """Test state display methods"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Test state display methods
        from_state_display = state_log.get_from_state_persian()
        to_state_display = state_log.get_to_state_persian()
        
        self.assertIsNotNone(from_state_display)
        self.assertIsNotNone(to_state_display)
        
        # Check that displays are Persian strings
        self.assertIsInstance(from_state_display, str)
        self.assertIsInstance(to_state_display, str)
        
        # Check that displays contain Persian characters
        self.assertTrue(any('\u0600' <= char <= '\u06FF' for char in from_state_display))
        self.assertTrue(any('\u0600' <= char <= '\u06FF' for char in to_state_display))
    
    def test_state_log_transaction_relationship(self):
        """Test state log transaction relationship"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Test that transaction relationship works
        self.assertEqual(state_log.transaction, self.transaction)
        self.assertIn(state_log, self.transaction.state_logs.all())
    
    def test_state_log_user_relationship(self):
        """Test state log user relationship"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Test that user relationship works
        self.assertEqual(state_log.changed_by, self.user)
        self.assertIn(state_log, self.user.changed_state_logs.all())
    
    def test_state_log_ordering(self):
        """Test state log ordering by timestamp"""
        # Create multiple state logs with different timestamps
        state_log1 = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Wait a moment to ensure different timestamps
        import time
        time.sleep(0.1)
        
        state_log2 = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_TREASURY,
            to_state=Transaction.STATE_WAITING_SANDOGH,
            changed_by=self.user
        )
        
        # Test ordering
        logs = TransactionStateLog.objects.filter(transaction=self.transaction).order_by('changed_at')
        self.assertEqual(logs[0], state_log1)
        self.assertEqual(logs[1], state_log2)
    
    def test_state_log_notes_optional(self):
        """Test that notes field is optional"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
            # No notes provided
        )
        
        self.assertIsNone(state_log.notes)
    
    def test_state_log_notes_with_content(self):
        """Test state log with notes content"""
        notes = 'Transaction approved by finance manager after review'
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user,
            notes=notes
        )
        
        self.assertEqual(state_log.notes, notes)
    
    def test_state_log_string_representation(self):
        """Test state log string representation"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        str_repr = str(state_log)
        self.assertIn(str(self.transaction.id), str_repr)
        self.assertIn(Transaction.STATE_WAITING_FINANCE_MANAGER, str_repr)
        self.assertIn(Transaction.STATE_WAITING_TREASURY, str_repr)
    
    def test_state_log_admin_display_methods(self):
        """Test admin display methods for state log"""
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Test admin display methods
        transaction_code = state_log.get_transaction_code()
        transaction_kind = state_log.get_transaction_kind_persian()
        transaction_amount = state_log.get_transaction_amount()
        
        self.assertIsNotNone(transaction_code)
        self.assertIsNotNone(transaction_kind)
        self.assertIsNotNone(transaction_amount)
        
        # Check that transaction code is displayed
        self.assertEqual(transaction_code, self.transaction.transaction_code)
        
        # Check that transaction kind is in Persian
        self.assertIsInstance(transaction_kind, str)
        self.assertTrue(any('\u0600' <= char <= '\u06FF' for char in transaction_kind))
        
        # Check that transaction amount is formatted
        self.assertIsInstance(transaction_amount, str)
        self.assertIn('100,000.00', transaction_amount)
    
    def test_state_log_with_none_transaction(self):
        """Test state log with None transaction"""
        state_log = TransactionStateLog.objects.create(
            transaction=None,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Test that admin display methods handle None transaction
        transaction_code = state_log.get_transaction_code()
        transaction_kind = state_log.get_transaction_kind_persian()
        transaction_amount = state_log.get_transaction_amount()
        
        self.assertEqual(transaction_code, '-')
        self.assertEqual(transaction_kind, '-')
        self.assertEqual(transaction_amount, '-')
    
    def test_state_log_workflow_progression(self):
        """Test state log creation during workflow progression"""
        # Simulate workflow progression
        states = [
            Transaction.STATE_WAITING_FINANCE_MANAGER,
            Transaction.STATE_WAITING_TREASURY,
            Transaction.STATE_WAITING_SANDOGH,
            Transaction.STATE_VERIFIED_KHAZANEDAR,
            Transaction.STATE_DONE
        ]
        
        # Create state logs for each transition
        for i in range(len(states) - 1):
            TransactionStateLog.objects.create(
                transaction=self.transaction,
                from_state=states[i],
                to_state=states[i + 1],
                changed_by=self.user,
                notes=f'Transition from {states[i]} to {states[i + 1]}'
            )
        
        # Verify all state logs were created
        logs = TransactionStateLog.objects.filter(transaction=self.transaction)
        self.assertEqual(logs.count(), 4)  # 4 transitions
        
        # Verify state progression
        log_states = list(logs.values_list('from_state', 'to_state'))
        expected_states = [
            (Transaction.STATE_WAITING_FINANCE_MANAGER, Transaction.STATE_WAITING_TREASURY),
            (Transaction.STATE_WAITING_TREASURY, Transaction.STATE_WAITING_SANDOGH),
            (Transaction.STATE_WAITING_SANDOGH, Transaction.STATE_VERIFIED_KHAZANEDAR),
            (Transaction.STATE_VERIFIED_KHAZANEDAR, Transaction.STATE_DONE)
        ]
        self.assertEqual(log_states, expected_states)
    
    def test_state_log_signal_integration(self):
        """Test state log creation through signals"""
        # Change transaction state to trigger signal
        self.transaction.state = Transaction.STATE_WAITING_TREASURY
        self.transaction.save()
        
        # Check that state log was created automatically
        logs = TransactionStateLog.objects.filter(transaction=self.transaction)
        self.assertGreater(logs.count(), 0)
        
        # Check that the log contains the state change
        latest_log = logs.order_by('-changed_at').first()
        self.assertEqual(latest_log.to_state, Transaction.STATE_WAITING_TREASURY)
    
    def test_state_log_multiple_transactions(self):
        """Test state logs for multiple transactions"""
        # Create another transaction
        transaction2 = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('50000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Create state logs for both transactions
        TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        TransactionStateLog.objects.create(
            transaction=transaction2,
            from_state=Transaction.STATE_WAITING_TREASURY,
            to_state=Transaction.STATE_WAITING_SANDOGH,
            changed_by=self.user
        )
        
        # Verify logs are separate
        logs1 = TransactionStateLog.objects.filter(transaction=self.transaction)
        logs2 = TransactionStateLog.objects.filter(transaction=transaction2)
        
        self.assertEqual(logs1.count(), 1)
        self.assertEqual(logs2.count(), 1)
        self.assertNotEqual(logs1.first(), logs2.first())
    
    def test_state_log_validation(self):
        """Test state log validation"""
        # Test with valid data
        state_log = TransactionStateLog(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user
        )
        
        # Should not raise validation error
        state_log.full_clean()
    
    def test_state_log_unicode_handling(self):
        """Test state log with Unicode characters in notes"""
        unicode_notes = 'تایید تراکنش توسط مدیر مالی - تأیید شده'
        state_log = TransactionStateLog.objects.create(
            transaction=self.transaction,
            from_state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            to_state=Transaction.STATE_WAITING_TREASURY,
            changed_by=self.user,
            notes=unicode_notes
        )
        
        self.assertEqual(state_log.notes, unicode_notes)
        
        # Test that Unicode is preserved in string representation
        str_repr = str(state_log)
        self.assertIn(unicode_notes, str_repr)
