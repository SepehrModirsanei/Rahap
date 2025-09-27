"""
Withdrawal Receipt Validation Tests

This module tests the withdrawal receipt validation functionality to ensure:
- Receipt is required when withdrawal request is marked as done
- Receipt is not required for other states
- Validation works correctly in different scenarios

Test Coverage:
- Receipt requirement for done state
- No receipt requirement for other states
- Validation error messages
- Edge cases and error handling
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from finance.models import User, Account, Transaction
from finance.tests.test_config import FinanceTestCase


class WithdrawalReceiptValidationTests(FinanceTestCase):
    """Test withdrawal receipt validation functionality"""
    
    def setUp(self):
        """Set up test data for withdrawal receipt validation testing"""
        self.user = self.create_test_user('withdrawal_receipt_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
    
    def test_withdrawal_receipt_required_when_done(self):
        """Test that receipt is required when withdrawal request is marked as done"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456',
            state=Transaction.STATE_DONE
            # No receipt provided
        )
        
        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()
        
        self.assertIn('Receipt is required for withdrawal requests when marked as done', str(context.exception))
    
    def test_withdrawal_receipt_not_required_for_other_states(self):
        """Test that receipt is not required for withdrawal requests in other states"""
        states = [
            Transaction.STATE_WAITING_FINANCE_MANAGER,
            Transaction.STATE_WAITING_TREASURY,
            Transaction.STATE_WAITING_SANDOGH,
            Transaction.STATE_VERIFIED_KHAZANEDAR,
            Transaction.STATE_APPROVED_BY_FINANCE_MANAGER,
            Transaction.STATE_APPROVED_BY_SANDOGH
        ]
        
        for state in states:
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_WITHDRAWAL_REQUEST,
                withdrawal_card_number='1234567890123456',
                state=state
                # No receipt provided
            )
            
            # Should not raise validation error
            transaction.full_clean()
    
    def test_withdrawal_receipt_validation_with_receipt(self):
        """Test that withdrawal request with receipt passes validation when done"""
        # Create a mock receipt (in real scenario, this would be an uploaded file)
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456',
            state=Transaction.STATE_DONE,
            receipt='receipts/test_receipt.jpg'  # Mock receipt path
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_withdrawal_receipt_validation_with_sheba(self):
        """Test that withdrawal request with SHEBA number requires receipt when done"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_sheba_number='IR1234567890123456789012',
            state=Transaction.STATE_DONE
            # No receipt provided
        )
        
        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()
        
        self.assertIn('Receipt is required for withdrawal requests when marked as done', str(context.exception))
    
    def test_withdrawal_receipt_validation_with_sheba_and_receipt(self):
        """Test that withdrawal request with SHEBA number and receipt passes validation when done"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_sheba_number='IR1234567890123456789012',
            state=Transaction.STATE_DONE,
            receipt='receipts/test_receipt.jpg'  # Mock receipt path
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_credit_increase_no_receipt_requirement(self):
        """Test that credit increase transactions don't require receipt validation"""
        transaction = Transaction(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
            # No receipt provided
        )
        
        # Should not raise validation error (credit increase doesn't require receipt)
        transaction.full_clean()
    
    def test_account_transfer_no_receipt_requirement(self):
        """Test that account transfer transactions don't require receipt validation"""
        usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
        
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            state=Transaction.STATE_DONE
            # No receipt provided
        )
        
        # Should not raise validation error (account transfer doesn't require receipt)
        transaction.full_clean()
    
    def test_withdrawal_receipt_validation_error_message(self):
        """Test that the validation error message is clear and helpful"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456',
            state=Transaction.STATE_DONE
            # No receipt provided
        )
        
        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()
        
        error_message = str(context.exception)
        self.assertIn('Receipt is required for withdrawal requests when marked as done', error_message)
        self.assertIn('receipt', error_message.lower())
    
    def test_withdrawal_receipt_validation_with_empty_receipt(self):
        """Test that withdrawal request with empty receipt fails validation when done"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456',
            state=Transaction.STATE_DONE,
            receipt=''  # Empty receipt
        )
        
        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()
        
        self.assertIn('Receipt is required for withdrawal requests when marked as done', str(context.exception))
    
    def test_withdrawal_receipt_validation_with_none_receipt(self):
        """Test that withdrawal request with None receipt fails validation when done"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456',
            state=Transaction.STATE_DONE,
            receipt=None  # None receipt
        )
        
        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()
        
        self.assertIn('Receipt is required for withdrawal requests when marked as done', str(context.exception))
    
    def test_withdrawal_receipt_validation_state_transition(self):
        """Test that receipt validation works correctly during state transitions"""
        # Create withdrawal request in waiting state (no receipt required)
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456',
            state=Transaction.STATE_WAITING_FINANCE_MANAGER
        )
        
        # Should not raise validation error
        transaction.full_clean()
        
        # Try to change state to done without receipt
        transaction.state = Transaction.STATE_DONE
        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()
        
        self.assertIn('Receipt is required for withdrawal requests when marked as done', str(context.exception))
        
        # Add receipt and try again
        transaction.receipt = 'receipts/test_receipt.jpg'
        transaction.full_clean()  # Should not raise validation error
    
    def test_withdrawal_receipt_validation_multiple_withdrawals(self):
        """Test that receipt validation works for multiple withdrawal requests"""
        # Create multiple withdrawal requests
        for i in range(3):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_WITHDRAWAL_REQUEST,
                withdrawal_card_number='1234567890123456',
                state=Transaction.STATE_DONE
                # No receipt provided
            )
            
            with self.assertRaises(ValidationError) as context:
                transaction.full_clean()
            
            self.assertIn('Receipt is required for withdrawal requests when marked as done', str(context.exception))
    
    def test_withdrawal_receipt_validation_different_amounts(self):
        """Test that receipt validation works for different withdrawal amounts"""
        amounts = [Decimal('1000.00'), Decimal('100000.00'), Decimal('1000000.00')]
        
        for amount in amounts:
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=amount,
                kind=Transaction.KIND_WITHDRAWAL_REQUEST,
                withdrawal_card_number='1234567890123456',
                state=Transaction.STATE_DONE
                # No receipt provided
            )
            
            with self.assertRaises(ValidationError) as context:
                transaction.full_clean()
            
            self.assertIn('Receipt is required for withdrawal requests when marked as done', str(context.exception))
