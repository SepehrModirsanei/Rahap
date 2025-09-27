"""
Transaction State Workflow Tests

This module tests the complete transaction state workflow system including:
- Initial state assignment based on transaction kind
- State transitions and workflow progression
- Admin workflow actions and permissions
- State log creation and tracking
- Workflow completion and validation

Test Coverage:
- Credit increase workflow (waiting_treasury → waiting_sandogh → verified_khazanedar → done)
- Withdrawal request workflow (waiting_finance_manager → waiting_treasury → waiting_sandogh → verified_khazanedar → done)
- State transition validation
- Admin action permissions
- State log creation for each transition
- Workflow completion requirements
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from finance.models import User, Account, Transaction, TransactionStateLog
from finance.tests.test_config import FinanceTestCase


class TransactionStateWorkflowTests(FinanceTestCase):
    """Test comprehensive transaction state workflow system"""
    
    def setUp(self):
        """Set up test data for workflow testing"""
        self.user = self.create_test_user('workflow_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
    
    def test_credit_increase_initial_state(self):
        """Test that credit increase transactions start in waiting_treasury state"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Should automatically be set to waiting_treasury state
        self.assertEqual(transaction.state, Transaction.STATE_WAITING_TREASURY)
        self.assertFalse(transaction.applied)  # Should not be applied yet
    
    def test_withdrawal_request_initial_state(self):
        """Test that withdrawal requests start in waiting_finance_manager state"""
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST
        )
        
        # Should automatically be set to waiting_finance_manager state
        self.assertEqual(transaction.state, Transaction.STATE_WAITING_FINANCE_MANAGER)
        self.assertFalse(transaction.applied)  # Should not be applied yet
    
    def test_account_transfer_initial_state(self):
        """Test that account transfers start in done state (auto-applied)"""
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00')
        )
        
        # Should automatically be set to done state and applied
        self.assertEqual(transaction.state, Transaction.STATE_DONE)
        self.assertTrue(transaction.applied)  # Should be auto-applied
    
    def test_credit_increase_workflow_progression(self):
        """Test complete credit increase workflow progression"""
        # Create credit increase transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Step 1: Treasury admin approves (waiting_treasury → waiting_sandogh)
        transaction.state = Transaction.STATE_WAITING_SANDOGH
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_WAITING_TREASURY, Transaction.STATE_WAITING_SANDOGH)
        
        # Step 2: Sandogh admin verifies (waiting_sandogh → verified_khazanedar)
        transaction.state = Transaction.STATE_VERIFIED_KHAZANEDAR
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_WAITING_SANDOGH, Transaction.STATE_VERIFIED_KHAZANEDAR)
        
        # Step 3: Operation admin completes (verified_khazanedar → done)
        transaction.state = Transaction.STATE_DONE
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_VERIFIED_KHAZANEDAR, Transaction.STATE_DONE)
        
        # Verify transaction is now applied
        self.assertTrue(transaction.applied)
    
    def test_withdrawal_request_workflow_progression(self):
        """Test complete withdrawal request workflow progression"""
        # Create withdrawal request transaction
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456'  # Add required card number
        )
        
        # Step 1: Finance manager approves (waiting_finance_manager → waiting_treasury)
        transaction.state = Transaction.STATE_WAITING_TREASURY
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_WAITING_FINANCE_MANAGER, Transaction.STATE_WAITING_TREASURY)
        
        # Step 2: Treasury admin approves (waiting_treasury → waiting_sandogh)
        transaction.state = Transaction.STATE_WAITING_SANDOGH
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_WAITING_TREASURY, Transaction.STATE_WAITING_SANDOGH)
        
        # Step 3: Sandogh admin verifies (waiting_sandogh → verified_khazanedar)
        transaction.state = Transaction.STATE_VERIFIED_KHAZANEDAR
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_WAITING_SANDOGH, Transaction.STATE_VERIFIED_KHAZANEDAR)
        
        # Step 4: Operation admin completes with receipt (verified_khazanedar → done)
        transaction.state = Transaction.STATE_DONE
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_VERIFIED_KHAZANEDAR, Transaction.STATE_DONE)
        
        # Verify transaction is now applied
        self.assertTrue(transaction.applied)
    
    def test_transaction_rejection_workflow(self):
        """Test that transactions can be rejected at any stage"""
        # Create credit increase transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Reject at treasury stage
        transaction.state = Transaction.STATE_REJECTED
        transaction.save()
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_WAITING_TREASURY, Transaction.STATE_REJECTED)
        
        # Verify transaction is not applied
        self.assertFalse(transaction.applied)
    
    def test_workflow_state_advancement(self):
        """Test the advance_state method for workflow progression"""
        # Create credit increase transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Test state advancement
        self.assertEqual(transaction.state, Transaction.STATE_WAITING_TREASURY)
        
        # Advance to next state
        transaction.advance_state()
        self.assertEqual(transaction.state, Transaction.STATE_WAITING_SANDOGH)
        
        # Advance to next state
        transaction.advance_state()
        self.assertEqual(transaction.state, Transaction.STATE_VERIFIED_KHAZANEDAR)
        
        # Advance to final state
        transaction.advance_state()
        self.assertEqual(transaction.state, Transaction.STATE_DONE)
        
        # Should not advance further
        transaction.advance_state()
        self.assertEqual(transaction.state, Transaction.STATE_DONE)
    
    def test_workflow_transaction_filtering(self):
        """Test that only workflow transactions require state progression"""
        # Create workflow transaction (credit increase)
        workflow_transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Create non-workflow transaction (account transfer)
        non_workflow_transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00')
        )
        
        # Workflow transaction should not be applied in initial state
        self.assertFalse(workflow_transaction.applied)
        
        # Non-workflow transaction should be auto-applied
        self.assertTrue(non_workflow_transaction.applied)
    
    def test_state_log_creation_on_save(self):
        """Test that state logs are created automatically on state changes"""
        # Create transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Change state and save
        transaction.state = Transaction.STATE_WAITING_SANDOGH
        transaction.save()
        
        # Verify state log was created
        self.assert_transaction_state_log_created(transaction, Transaction.STATE_WAITING_TREASURY, Transaction.STATE_WAITING_SANDOGH)
    
    def test_multiple_state_changes_logging(self):
        """Test that multiple state changes create multiple logs"""
        # Create transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Make multiple state changes
        transaction.state = Transaction.STATE_WAITING_SANDOGH
        transaction.save()
        
        transaction.state = Transaction.STATE_VERIFIED_KHAZANEDAR
        transaction.save()
        
        transaction.state = Transaction.STATE_DONE
        transaction.save()
        
        # Verify all state logs were created
        logs = TransactionStateLog.objects.filter(transaction=transaction)
        # There might be more logs due to initial state setting
        self.assertGreaterEqual(logs.count(), 3)
        
        # Verify log sequence - check that our expected transitions exist
        log_states = list(logs.values_list('from_state', 'to_state'))
        expected_transitions = [
            (Transaction.STATE_WAITING_TREASURY, Transaction.STATE_WAITING_SANDOGH),
            (Transaction.STATE_WAITING_SANDOGH, Transaction.STATE_VERIFIED_KHAZANEDAR),
            (Transaction.STATE_VERIFIED_KHAZANEDAR, Transaction.STATE_DONE)
        ]
        
        # Check that all expected transitions exist in the logs
        for expected_transition in expected_transitions:
            self.assertIn(expected_transition, log_states)
    
    def test_workflow_completion_requirements(self):
        """Test that workflow transactions require specific completion steps"""
        # Create withdrawal request
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456'  # Add required card number
        )
        
        # Should not be applied until reaching done state
        self.assertFalse(transaction.applied)
        
        # Complete workflow
        transaction.state = Transaction.STATE_DONE
        transaction.save()
        
        # Now should be applied
        self.assertTrue(transaction.applied)
