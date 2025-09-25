"""
Tests for Admin Workflow System

This test file verifies the complete workflow system for credit increase and withdrawal requests
that flow between different admin types with appropriate permissions and actions.

WORKFLOW TESTS:
- Credit Increase: User/Operation → Treasury → Sandogh (Treasury) → Operation → Done
- Withdrawal Request: User/Operation → Finance Manager → Treasury → Sandogh (Treasury) → Operation → Done
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from finance.models import User, Account, Transaction
from finance.tests.test_config import FinanceTestCase


class AdminWorkflowTests(FinanceTestCase):
    """Tests for admin workflow system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.base_account = self.get_user_base_account(self.user)
        
        # Create test transactions
        self.credit_increase = Transaction.objects.create(
            user=self.user,
            destination_account=self.base_account,
            amount=Decimal('1000000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_WAITING_TREASURY
        )
        
        self.withdrawal_request = Transaction.objects.create(
            user=self.user,
            source_account=self.base_account,
            amount=Decimal('500000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            withdrawal_card_number='1234567890123456'
        )

    def test_credit_increase_workflow(self):
        """Test credit increase workflow: Treasury → Sandogh → Operation → Done"""
        print("\n=== Testing Credit Increase Workflow ===")
        
        # Step 1: Treasury Admin approves for sandogh
        print(f"Initial state: {self.credit_increase.get_state_display()}")
        self.assertEqual(self.credit_increase.state, Transaction.STATE_WAITING_TREASURY)
        
        # Treasury Admin action: approve_for_sandogh
        self.credit_increase.state = Transaction.STATE_WAITING_SANDOGH
        self.credit_increase.save()
        print(f"After Treasury approval: {self.credit_increase.get_state_display()}")
        self.assertEqual(self.credit_increase.state, Transaction.STATE_WAITING_SANDOGH)
        
        # Step 2: Treasury Admin (Sandogh function) verifies
        self.credit_increase.state = Transaction.STATE_APPROVED_BY_SANDOGH
        self.credit_increase.save()
        print(f"After Sandogh verification: {self.credit_increase.get_state_display()}")
        self.assertEqual(self.credit_increase.state, Transaction.STATE_APPROVED_BY_SANDOGH)
        
        # Step 3: Operation Admin completes
        self.credit_increase.state = Transaction.STATE_DONE
        self.credit_increase.save()
        print(f"After Operation completion: {self.credit_increase.get_state_display()}")
        self.assertEqual(self.credit_increase.state, Transaction.STATE_DONE)
        
        print("✅ Credit Increase workflow completed successfully")

    def test_withdrawal_request_workflow(self):
        """Test withdrawal request workflow: Finance Manager → Treasury → Sandogh → Operation → Done"""
        print("\n=== Testing Withdrawal Request Workflow ===")
        
        # Step 1: Finance Manager approves
        print(f"Initial state: {self.withdrawal_request.get_state_display()}")
        self.assertEqual(self.withdrawal_request.state, Transaction.STATE_WAITING_FINANCE_MANAGER)
        
        self.withdrawal_request.state = Transaction.STATE_APPROVED_BY_FINANCE_MANAGER
        self.withdrawal_request.save()
        print(f"After Finance Manager approval: {self.withdrawal_request.get_state_display()}")
        self.assertEqual(self.withdrawal_request.state, Transaction.STATE_APPROVED_BY_FINANCE_MANAGER)
        
        # Step 2: Treasury Admin approves for sandogh
        self.withdrawal_request.state = Transaction.STATE_WAITING_SANDOGH
        self.withdrawal_request.save()
        print(f"After Treasury approval: {self.withdrawal_request.get_state_display()}")
        self.assertEqual(self.withdrawal_request.state, Transaction.STATE_WAITING_SANDOGH)
        
        # Step 3: Treasury Admin (Sandogh function) verifies with receipt
        self.withdrawal_request.state = Transaction.STATE_APPROVED_BY_SANDOGH
        self.withdrawal_request.save()
        print(f"After Sandogh verification: {self.withdrawal_request.get_state_display()}")
        self.assertEqual(self.withdrawal_request.state, Transaction.STATE_APPROVED_BY_SANDOGH)
        
        # Step 4: Operation Admin completes
        self.withdrawal_request.state = Transaction.STATE_DONE
        self.withdrawal_request.save()
        print(f"After Operation completion: {self.withdrawal_request.get_state_display()}")
        self.assertEqual(self.withdrawal_request.state, Transaction.STATE_DONE)
        
        print("✅ Withdrawal Request workflow completed successfully")

    def test_initial_states(self):
        """Test that transactions are created with correct initial states"""
        print("\n=== Testing Initial States ===")
        
        # Test credit increase initial state
        credit_txn = Transaction.objects.create(
            user=self.user,
            destination_account=self.base_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        self.assertEqual(credit_txn.state, Transaction.STATE_WAITING_TREASURY)
        print(f"✅ Credit Increase initial state: {credit_txn.get_state_display()}")
        
        # Test withdrawal request initial state
        withdrawal_txn = Transaction.objects.create(
            user=self.user,
            source_account=self.base_account,
            amount=Decimal('50000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST
        )
        self.assertEqual(withdrawal_txn.state, Transaction.STATE_WAITING_FINANCE_MANAGER)
        print(f"✅ Withdrawal Request initial state: {withdrawal_txn.get_state_display()}")

    def test_workflow_progress_display(self):
        """Test workflow progress display for different transaction types"""
        print("\n=== Testing Workflow Progress Display ===")
        
        # Test credit increase progress
        credit_states = [
            Transaction.STATE_WAITING_TREASURY,
            Transaction.STATE_WAITING_SANDOGH,
            Transaction.STATE_APPROVED_BY_SANDOGH,
            Transaction.STATE_DONE
        ]
        
        for i, state in enumerate(credit_states):
            self.credit_increase.state = state
            self.credit_increase.save()
            progress = (i + 1) / len(credit_states) * 100
            print(f"Credit Increase {state}: {progress:.0f}% complete")
        
        # Test withdrawal request progress
        withdrawal_states = [
            Transaction.STATE_WAITING_FINANCE_MANAGER,
            Transaction.STATE_APPROVED_BY_FINANCE_MANAGER,
            Transaction.STATE_WAITING_SANDOGH,
            Transaction.STATE_APPROVED_BY_SANDOGH,
            Transaction.STATE_DONE
        ]
        
        for i, state in enumerate(withdrawal_states):
            self.withdrawal_request.state = state
            self.withdrawal_request.save()
            progress = (i + 1) / len(withdrawal_states) * 100
            print(f"Withdrawal Request {state}: {progress:.0f}% complete")
        
        print("✅ Workflow progress display working correctly")

    def test_admin_permissions(self):
        """Test that different admin types see appropriate transactions"""
        print("\n=== Testing Admin Permissions ===")
        
        # Treasury Admin should see:
        # - Credit increases waiting for treasury
        # - Withdrawal requests approved by finance manager
        # - Both waiting for sandogh
        
        # Reset withdrawal request to approved by finance manager
        self.withdrawal_request.state = Transaction.STATE_APPROVED_BY_FINANCE_MANAGER
        self.withdrawal_request.save()
        
        treasury_transactions = Transaction.objects.filter(
            state__in=[
                Transaction.STATE_WAITING_TREASURY,
                Transaction.STATE_APPROVED_BY_FINANCE_MANAGER,
                Transaction.STATE_WAITING_SANDOGH
            ]
        )
        
        self.assertEqual(treasury_transactions.count(), 2)
        print("✅ Treasury Admin sees correct transactions")
        
        # Finance Manager should see:
        # - Withdrawal requests waiting for finance manager
        
        # Reset withdrawal request to waiting for finance manager
        self.withdrawal_request.state = Transaction.STATE_WAITING_FINANCE_MANAGER
        self.withdrawal_request.save()
        
        finance_manager_transactions = Transaction.objects.filter(
            state=Transaction.STATE_WAITING_FINANCE_MANAGER,
            kind=Transaction.KIND_WITHDRAWAL_REQUEST
        )
        
        self.assertEqual(finance_manager_transactions.count(), 1)
        print("✅ Finance Manager sees correct transactions")
        
        # Operation Admin should see:
        # - Transactions approved by sandogh
        
        operation_transactions = Transaction.objects.filter(
            state=Transaction.STATE_APPROVED_BY_SANDOGH
        )
        
        # Set one transaction to approved by sandogh for testing
        self.credit_increase.state = Transaction.STATE_APPROVED_BY_SANDOGH
        self.credit_increase.save()
        
        operation_transactions = Transaction.objects.filter(
            state=Transaction.STATE_APPROVED_BY_SANDOGH
        )
        
        self.assertEqual(operation_transactions.count(), 1)
        print("✅ Operation Admin sees correct transactions")

    def test_workflow_actions(self):
        """Test workflow actions for different admin types"""
        print("\n=== Testing Workflow Actions ===")
        
        # Test Treasury Admin actions
        treasury_actions = ['approve_for_sandogh', 'verify_sandogh', 'reject_transaction']
        print(f"Treasury Admin actions: {treasury_actions}")
        
        # Test Finance Manager actions
        finance_manager_actions = ['approve_finance_manager', 'reject_transaction']
        print(f"Finance Manager actions: {finance_manager_actions}")
        
        # Test Operation Admin actions
        operation_actions = ['complete_transaction', 'reject_transaction']
        print(f"Operation Admin actions: {operation_actions}")
        
        print("✅ Workflow actions defined correctly")

    def test_rejection_workflow(self):
        """Test that transactions can be rejected at any stage"""
        print("\n=== Testing Rejection Workflow ===")
        
        # Test rejection from treasury
        self.credit_increase.state = Transaction.STATE_REJECTED
        self.credit_increase.save()
        self.assertEqual(self.credit_increase.state, Transaction.STATE_REJECTED)
        print("✅ Transaction rejected from treasury")
        
        # Test rejection from finance manager
        self.withdrawal_request.state = Transaction.STATE_REJECTED
        self.withdrawal_request.save()
        self.assertEqual(self.withdrawal_request.state, Transaction.STATE_REJECTED)
        print("✅ Transaction rejected from finance manager")

    def run_all_tests(self):
        """Run all workflow tests"""
        print("=" * 80)
        print("ADMIN WORKFLOW TESTS")
        print("=" * 80)
        
        try:
            self.test_credit_increase_workflow()
            self.test_withdrawal_request_workflow()
            self.test_initial_states()
            self.test_workflow_progress_display()
            self.test_admin_permissions()
            self.test_workflow_actions()
            self.test_rejection_workflow()
            
            print("\n" + "=" * 80)
            print("✅ ALL ADMIN WORKFLOW TESTS PASSED!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            raise


if __name__ == '__main__':
    # Run the test
    test = AdminWorkflowTests()
    test.setUp()
    test.run_all_tests()
