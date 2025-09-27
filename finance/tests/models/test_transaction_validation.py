"""
Transaction Validation Tests

This module tests transaction model validation functionality including:
- Basic field validation (amount, exchange rate, etc.)
- Required field validation
- Business rule validation
- Edge cases and boundary conditions
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from finance.models import User, Account, Transaction
from finance.tests.test_config import FinanceTestCase


class TransactionValidationTests(FinanceTestCase):
    """Test transaction model validation functionality"""
    
    def setUp(self):
        """Set up test data for transaction validation testing"""
        self.user = self.create_test_user('transaction_validation_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
    
    def test_transaction_validation_insufficient_balance(self):
        """Test transaction validation with insufficient balance"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('2000000.00'),  # More than available balance
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
    
    def test_transaction_validation_missing_required_fields(self):
        """Test transaction validation with missing required fields"""
        # Test missing user
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                source_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
        
        # Test missing source account
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
        
        # Test missing amount
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
    
    def test_transaction_validation_negative_amount(self):
        """Test transaction validation with negative amount"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('-100000.00'),  # Negative amount
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
    
    def test_transaction_validation_zero_amount(self):
        """Test transaction validation with zero amount"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('0.00'),  # Zero amount
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
    
    def test_transaction_validation_invalid_exchange_rate(self):
        """Test transaction validation with invalid exchange rate"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                destination_account=self.usd_account,
                amount=Decimal('100000.00'),
                exchange_rate=Decimal('-1.0'),  # Negative exchange rate
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
    
    def test_transaction_validation_zero_exchange_rate(self):
        """Test transaction validation with zero exchange rate"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                destination_account=self.usd_account,
                amount=Decimal('100000.00'),
                exchange_rate=Decimal('0.00'),  # Zero exchange rate
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            transaction.full_clean()
    
    def test_transaction_validation_withdrawal_missing_bank_info(self):
        """Test transaction validation for withdrawal with missing bank info"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_WITHDRAWAL_REQUEST
                # Missing withdrawal_card_number and withdrawal_sheba_number
            )
            transaction.full_clean()
    
    def test_transaction_validation_withdrawal_with_bank_info(self):
        """Test transaction validation for withdrawal with bank info"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456'
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_withdrawal_with_sheba(self):
        """Test transaction validation for withdrawal with SHEBA number"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_sheba_number='IR1234567890123456789012'
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_credit_increase_missing_destination(self):
        """Test transaction validation for credit increase with missing destination"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_CREDIT_INCREASE
                # Missing destination_account
            )
            transaction.full_clean()
    
    def test_transaction_validation_credit_increase_with_destination(self):
        """Test transaction validation for credit increase with destination"""
        transaction = Transaction(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_profit_transaction_missing_destination(self):
        """Test transaction validation for profit transaction with missing destination"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_PROFIT_TRANSACTION
                # Missing destination_account
            )
            transaction.full_clean()
    
    def test_transaction_validation_profit_transaction_with_destination(self):
        """Test transaction validation for profit transaction with destination"""
        transaction = Transaction(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_PROFIT_TRANSACTION
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_account_transfer_missing_accounts(self):
        """Test transaction validation for account transfer with missing accounts"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
                # Missing source_account and destination_account
            )
            transaction.full_clean()
    
    def test_transaction_validation_account_transfer_with_accounts(self):
        """Test transaction validation for account transfer with accounts"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_future_scheduled(self):
        """Test transaction validation with future scheduled date"""
        from datetime import datetime, timedelta
        
        future_date = datetime.now() + timedelta(days=30)
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            scheduled_for=future_date
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_past_scheduled(self):
        """Test transaction validation with past scheduled date"""
        from datetime import datetime, timedelta
        
        past_date = datetime.now() - timedelta(days=30)
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            scheduled_for=past_date
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_invalid_state(self):
        """Test transaction validation with invalid state"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT,
                state='invalid_state'
            )
            transaction.full_clean()
    
    def test_transaction_validation_invalid_kind(self):
        """Test transaction validation with invalid kind"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                amount=Decimal('100000.00'),
                kind='invalid_kind'
            )
            transaction.full_clean()
    
    def test_transaction_validation_exchange_rate_bounds(self):
        """Test transaction validation with exchange rate bounds"""
        # Test very small exchange rate
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            exchange_rate=Decimal('0.000001'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
        )
        # Should not raise validation error
        transaction.full_clean()
        
        # Test very large exchange rate
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            exchange_rate=Decimal('999999.99'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_amount_bounds(self):
        """Test transaction validation with amount bounds"""
        # Test very small amount
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('0.01'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
        )
        # Should not raise validation error
        transaction.full_clean()
        
        # Test very large amount
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('999999999999999.99'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_decimal_precision(self):
        """Test transaction validation with decimal precision"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.123456'),
            exchange_rate=Decimal('3.123456'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_unicode_handling(self):
        """Test transaction validation with unicode handling"""
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            comment='Test comment with unicode: 测试'
        )
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_edge_case_amounts(self):
        """Test transaction validation with edge case amounts"""
        edge_cases = [
            Decimal('0.01'),      # Minimum positive amount
            Decimal('1.00'),      # Small amount
            Decimal('1000000.00'), # Normal amount
            Decimal('999999999999999.99'), # Very large amount
        ]
        
        for amount in edge_cases:
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                destination_account=self.usd_account,
                amount=amount,
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            # Should not raise validation error for valid amounts
            transaction.full_clean()
    
    def test_transaction_validation_edge_case_exchange_rates(self):
        """Test transaction validation with edge case exchange rates"""
        edge_cases = [
            Decimal('0.000001'),  # Very small exchange rate
            Decimal('1.00'),      # Normal exchange rate
            Decimal('1000.00'),   # Large exchange rate
            Decimal('999999.99'), # Very large exchange rate
        ]
        
        for rate in edge_cases:
            transaction = Transaction(
                user=self.user,
                source_account=self.rial_account,
                destination_account=self.usd_account,
                amount=Decimal('100000.00'),
                exchange_rate=rate,
                kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT
            )
            # Should not raise validation error for valid rates
            transaction.full_clean()
    
    def test_transaction_validation_complex_scenarios(self):
        """Test transaction validation with complex scenarios"""
        # Test with all fields set to edge values
        transaction = Transaction(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('999999999999999.99'),
            exchange_rate=Decimal('999999.99'),
            kind=Transaction.KIND_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_WAITING_TREASURY,
            comment='Complex test scenario with unicode: 测试'
        )
        # Should not raise validation error
        transaction.full_clean()
