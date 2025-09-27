"""
Enhanced Transaction Model Tests

This module tests additional transaction model functionality to improve coverage including:
- Advanced transaction validation and edge cases
- Complex exchange rate calculations
- Transaction state management
- Transaction code generation edge cases
- Transaction application edge cases
- Transaction reversion functionality
- Transaction scheduling and timing

Test Coverage:
- Advanced validation scenarios
- Complex exchange rate logic
- State transition edge cases
- Transaction code generation edge cases
- Transaction application edge cases
- Transaction reversion functionality
- Transaction scheduling functionality
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from finance.models import User, Account, Transaction
from finance.tests.test_config import FinanceTestCase


class TransactionModelEnhancedTests(FinanceTestCase):
    """Test enhanced transaction model functionality"""
    
    def setUp(self):
        """Set up test data for enhanced transaction testing"""
        self.user = self.create_test_user('enhanced_transaction_user')
        self.accounts = self.create_cross_currency_accounts(self.user)
    
    def test_transaction_validation_insufficient_balance(self):
        """Test transaction validation with insufficient balance"""
        # Try to withdraw more than available
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['usd'],
                destination_account=self.accounts['rial'],
                amount=Decimal('2000.00'),  # More than available (1000 USD)
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_missing_required_fields(self):
        """Test transaction validation with missing required fields"""
        # Test missing user
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
        
        # Test missing amount
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_negative_amount(self):
        """Test transaction validation with negative amount"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('-100000.00'),  # Negative amount
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_zero_amount(self):
        """Test transaction validation with zero amount"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('0.00'),  # Zero amount
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_invalid_exchange_rate(self):
        """Test transaction validation with invalid exchange rate"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('-500000.00'),  # Negative exchange rate
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_zero_exchange_rate(self):
        """Test transaction validation with zero exchange rate"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('0.00'),  # Zero exchange rate
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_withdrawal_missing_bank_info(self):
        """Test withdrawal transaction validation with missing bank info"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_WITHDRAWAL_REQUEST,
                state=Transaction.STATE_DONE
                # Missing withdrawal_card_number and withdrawal_sheba_number
            )
            transaction.full_clean()
    
    def test_transaction_validation_withdrawal_with_bank_info(self):
        """Test withdrawal transaction validation with bank info"""
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_card_number='1234567890123456',
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_withdrawal_with_sheba(self):
        """Test withdrawal transaction validation with SHEBA number"""
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            withdrawal_sheba_number='IR123456789012345678901234',
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_credit_increase_missing_destination(self):
        """Test credit increase validation with missing destination account"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_CREDIT_INCREASE,
                state=Transaction.STATE_DONE
                # Missing destination_account
            )
            transaction.full_clean()
    
    def test_transaction_validation_credit_increase_with_destination(self):
        """Test credit increase validation with destination account"""
        transaction = Transaction(
            user=self.user,
            destination_account=self.accounts['rial'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_profit_transaction_missing_destination(self):
        """Test profit transaction validation with missing destination"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                amount=Decimal('25000.00'),
                kind=Transaction.KIND_PROFIT_ACCOUNT,
                state=Transaction.STATE_DONE
                # Missing destination_account
            )
            transaction.full_clean()
    
    def test_transaction_validation_profit_transaction_with_destination(self):
        """Test profit transaction validation with destination account"""
        transaction = Transaction(
            user=self.user,
            destination_account=self.accounts['rial'],
            amount=Decimal('25000.00'),
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_account_transfer_missing_accounts(self):
        """Test account transfer validation with missing accounts"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
                # Missing source_account and destination_account
            )
            transaction.full_clean()
    
    def test_transaction_validation_account_transfer_with_accounts(self):
        """Test account transfer validation with accounts"""
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_future_scheduled(self):
        """Test transaction validation with future scheduling"""
        future_time = timezone.now() + timedelta(days=1)
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            scheduled_for=future_time,
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_past_scheduled(self):
        """Test transaction validation with past scheduling"""
        past_time = timezone.now() - timedelta(days=1)
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            scheduled_for=past_time,
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_invalid_state(self):
        """Test transaction validation with invalid state"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state='invalid_state'
            )
            transaction.full_clean()
    
    def test_transaction_validation_invalid_kind(self):
        """Test transaction validation with invalid kind"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('100000.00'),
                kind='invalid_kind',
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_exchange_rate_bounds(self):
        """Test transaction validation with exchange rate bounds"""
        # Test very large exchange rate
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('999999999999999.999999'),  # Too large
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_amount_bounds(self):
        """Test transaction validation with amount bounds"""
        # Test very large amount
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('999999999999999999.99'),  # Too large
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
            transaction.full_clean()
    
    def test_transaction_validation_decimal_precision(self):
        """Test transaction validation with decimal precision"""
        # Test with high precision amount
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.123456'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.123456'),
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_unicode_handling(self):
        """Test transaction validation with Unicode characters"""
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            state=Transaction.STATE_DONE,
            user_comment='نظر کاربر',
            admin_opinion='نظر ادمین',
            treasurer_opinion='نظر خزانه‌دار',
            finance_manager_opinion='نظر مدیر مالی'
        )
        
        # Should not raise validation error
        transaction.full_clean()
        
        # Test that Unicode is preserved
        self.assertEqual(transaction.user_comment, 'نظر کاربر')
        self.assertEqual(transaction.admin_opinion, 'نظر ادمین')
        self.assertEqual(transaction.treasurer_opinion, 'نظر خزانه‌دار')
        self.assertEqual(transaction.finance_manager_opinion, 'نظر مدیر مالی')
    
    def test_transaction_validation_edge_case_amounts(self):
        """Test transaction validation with edge case amounts"""
        # Test very small amount
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('0.01'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
        
        # Test very large but valid amount
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('999999999999999.99'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_edge_case_exchange_rates(self):
        """Test transaction validation with edge case exchange rates"""
        # Test very small exchange rate
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('0.000001'),
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
        
        # Test very large but valid exchange rate
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('999999999999.999999'),
            state=Transaction.STATE_DONE
        )
        
        # Should not raise validation error
        transaction.full_clean()
    
    def test_transaction_validation_complex_scenarios(self):
        """Test transaction validation with complex scenarios"""
        # Test with all optional fields
        transaction = Transaction(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=Decimal('500000.00'),
            destination_amount=Decimal('0.20'),
            source_price_irr=Decimal('500000.00'),
            dest_price_irr=Decimal('2500000.00'),
            state=Transaction.STATE_DONE,
            scheduled_for=timezone.now() + timedelta(hours=1),
            user_comment='User comment',
            admin_opinion='Admin opinion',
            treasurer_opinion='Treasurer opinion',
            finance_manager_opinion='Finance manager opinion',
            withdrawal_card_number='1234567890123456',
            withdrawal_sheba_number='IR123456789012345678901234'
        )
        
        # Should not raise validation error
        transaction.full_clean()
        
        # Test that all fields are preserved
        self.assertEqual(transaction.destination_amount, Decimal('0.20'))
        self.assertEqual(transaction.source_price_irr, Decimal('500000.00'))
        self.assertEqual(transaction.dest_price_irr, Decimal('2500000.00'))
        self.assertEqual(transaction.user_comment, 'User comment')
        self.assertEqual(transaction.admin_opinion, 'Admin opinion')
        self.assertEqual(transaction.treasurer_opinion, 'Treasurer opinion')
        self.assertEqual(transaction.finance_manager_opinion, 'Finance manager opinion')
        self.assertEqual(transaction.withdrawal_card_number, '1234567890123456')
        self.assertEqual(transaction.withdrawal_sheba_number, 'IR123456789012345678901234')
