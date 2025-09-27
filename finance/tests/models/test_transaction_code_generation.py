"""
Transaction Code Generation Tests

This module tests the transaction code generation system including:
- Unique code generation for different transaction types
- User prefix extraction and validation
- Persian date formatting in codes
- Daily sequence numbering per user and transaction kind
- Code uniqueness and collision prevention

Test Coverage:
- Code format validation (type-user_prefix-date-sequence)
- Uniqueness across different transaction types
- Daily sequence number increment
- User prefix extraction from UUID
- Persian date formatting
- Collision prevention for same-day transactions
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from finance.models import User, Account, Transaction
from finance.tests.test_config import FinanceTestCase


class TransactionCodeGenerationTests(FinanceTestCase):
    """Test comprehensive transaction code generation system"""
    
    def setUp(self):
        """Set up test data for code generation testing"""
        self.user = self.create_test_user('codegen_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
    
    def test_credit_increase_code_generation(self):
        """Test code generation for credit increase transactions"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Verify code format
        self.assertIsNotNone(transaction.transaction_code)
        self.assert_transaction_code_format(
            transaction.transaction_code,
            'In',  # Credit increase uses 'In' prefix
            self.user.short_user_id[:8]
        )
    
    def test_withdrawal_request_code_generation(self):
        """Test code generation for withdrawal request transactions"""
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST
        )
        
        # Verify code format
        self.assertIsNotNone(transaction.transaction_code)
        self.assert_transaction_code_format(
            transaction.transaction_code,
            'Out',  # Withdrawal request uses 'Out' prefix
            self.user.short_user_id[:8]
        )
    
    def test_account_transfer_code_generation(self):
        """Test code generation for account transfer transactions"""
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00')
        )
        
        # Verify code format
        self.assertIsNotNone(transaction.transaction_code)
        self.assert_transaction_code_format(
            transaction.transaction_code,
            'Transfer',  # Account transfer uses 'Transfer' prefix
            self.user.short_user_id[:8]
        )
    
    def test_profit_transaction_code_generation(self):
        """Test code generation for profit transactions"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('25000.00'),
            kind=Transaction.KIND_PROFIT_ACCOUNT
        )
        
        # Verify code format
        self.assertIsNotNone(transaction.transaction_code)
        self.assert_transaction_code_format(
            transaction.transaction_code,
            'Profit',  # Profit transaction uses 'Profit' prefix
            self.user.short_user_id[:8]
        )
    
    def test_daily_sequence_numbering(self):
        """Test that daily sequence numbers increment correctly"""
        # Create multiple transactions of same kind on same day
        transactions = []
        for i in range(3):
            transaction = Transaction.objects.create(
                user=self.user,
                destination_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_CREDIT_INCREASE
            )
            transactions.append(transaction)
        
        # Extract sequence numbers from codes
        sequence_numbers = []
        for transaction in transactions:
            code_parts = transaction.transaction_code.split('-')
            sequence_numbers.append(int(code_parts[3]))
        
        # Verify sequence numbers are sequential (1, 2, 3)
        self.assertEqual(sequence_numbers, [1, 2, 3])
    
    def test_different_transaction_kinds_separate_sequences(self):
        """Test that different transaction kinds have separate sequence numbers"""
        # Create transactions of different kinds
        credit_transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        withdrawal_transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST
        )
        
        # Extract sequence numbers
        credit_sequence = int(credit_transaction.transaction_code.split('-')[3])
        withdrawal_sequence = int(withdrawal_transaction.transaction_code.split('-')[3])
        
        # Both should start from 1 (separate sequences)
        self.assertEqual(credit_sequence, 1)
        self.assertEqual(withdrawal_sequence, 1)
    
    def test_different_users_separate_sequences(self):
        """Test that different users have separate sequence numbers"""
        # Create second user
        user2 = self.create_test_user('codegen_user2')
        rial_account2 = self.create_test_account(
            user2, 'Test Rial Account 2', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        
        # Create transactions for both users
        transaction1 = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        transaction2 = Transaction.objects.create(
            user=user2,
            destination_account=rial_account2,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Extract sequence numbers
        sequence1 = int(transaction1.transaction_code.split('-')[3])
        sequence2 = int(transaction2.transaction_code.split('-')[3])
        
        # Both should start from 1 (separate sequences per user)
        self.assertEqual(sequence1, 1)
        self.assertEqual(sequence2, 1)
    
    def test_code_uniqueness(self):
        """Test that generated codes are unique"""
        # Create multiple transactions
        transactions = []
        for i in range(5):
            transaction = Transaction.objects.create(
                user=self.user,
                destination_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_CREDIT_INCREASE
            )
            transactions.append(transaction)
        
        # Extract all codes
        codes = [txn.transaction_code for txn in transactions]
        
        # Verify all codes are unique
        self.assertEqual(len(codes), len(set(codes)))
    
    def test_user_prefix_extraction(self):
        """Test that user prefix is correctly extracted from UUID"""
        # Get user's short_user_id (first 8 chars of UUID)
        expected_prefix = self.user.short_user_id[:8]
        
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Extract prefix from code
        code_parts = transaction.transaction_code.split('-')
        actual_prefix = code_parts[1]
        
        # Verify prefix matches
        self.assertEqual(actual_prefix, expected_prefix)
    
    def test_persian_date_in_code(self):
        """Test that Persian date is correctly formatted in code"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Extract date from code
        code_parts = transaction.transaction_code.split('-')
        date_part = code_parts[2]
        
        # Verify date part is numeric (Persian date as number)
        self.assertTrue(date_part.isdigit())
        self.assertEqual(len(date_part), 8)  # YYYYMMDD format
    
    def test_code_generation_on_save(self):
        """Test that code is generated automatically on save"""
        # Create transaction without code
        transaction = Transaction(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        # Code should be None before save
        self.assertIsNone(transaction.transaction_code)
        
        # Save should generate code
        transaction.save()
        
        # Code should be generated after save
        self.assertIsNotNone(transaction.transaction_code)
    
    def test_code_regeneration_prevention(self):
        """Test that existing codes are not regenerated"""
        # Create transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        original_code = transaction.transaction_code
        
        # Save again
        transaction.save()
        
        # Code should remain the same
        self.assertEqual(transaction.transaction_code, original_code)
    
    def test_code_format_validation(self):
        """Test that generated codes follow the correct format"""
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        
        code = transaction.transaction_code
        
        # Verify format: type-user_prefix-date-sequence
        parts = code.split('-')
        self.assertEqual(len(parts), 4)
        
        # Part 0: transaction kind
        self.assertEqual(parts[0], 'In')
        
        # Part 1: user prefix (8 characters)
        self.assertEqual(len(parts[1]), 8)
        self.assertTrue(parts[1].isalnum())
        
        # Part 2: Persian date (8 digits)
        self.assertEqual(len(parts[2]), 8)
        self.assertTrue(parts[2].isdigit())
        
        # Part 3: sequence number (1 or more digits)
        self.assertTrue(parts[3].isdigit())
        self.assertGreaterEqual(int(parts[3]), 1)
