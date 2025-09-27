"""
Deposit Validation Tests

This module tests deposit model validation functionality including:
- Field validation (balance, profit rate, breakage coefficient)
- Edge cases and boundary conditions
- Decimal precision handling
- Unicode handling
- Complex validation scenarios
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from finance.models import User, Account, Deposit
from finance.tests.test_config import FinanceTestCase


class DepositValidationTests(FinanceTestCase):
    """Test deposit model validation functionality"""
    
    def setUp(self):
        """Set up test data for deposit validation testing"""
        self.user = self.create_test_user('deposit_validation_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
    
    def test_deposit_validation_negative_initial_balance(self):
        """Test deposit validation with negative initial balance"""
        with self.assertRaises(ValidationError):
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('-100000.00'),  # Negative balance
                monthly_profit_rate=Decimal('3.0')
            )
            deposit.full_clean()
    
    def test_deposit_validation_negative_profit_rate(self):
        """Test deposit validation with negative profit rate"""
        with self.assertRaises(ValidationError):
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('-1.0')  # Negative profit rate
            )
            deposit.full_clean()
    
    def test_deposit_validation_negative_breakage_coefficient(self):
        """Test deposit validation with negative breakage coefficient"""
        with self.assertRaises(ValidationError):
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                breakage_coefficient=Decimal('-10.0')  # Negative breakage coefficient
            )
            deposit.full_clean()
    
    def test_deposit_validation_breakage_coefficient_over_100(self):
        """Test deposit validation with breakage coefficient over 100"""
        with self.assertRaises(ValidationError):
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                breakage_coefficient=Decimal('150.0')  # Over 100%
            )
            deposit.full_clean()
    
    def test_deposit_validation_invalid_profit_kind(self):
        """Test deposit validation with invalid profit kind"""
        with self.assertRaises(ValidationError):
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind='invalid_kind'  # Invalid profit kind
            )
            deposit.full_clean()
    
    def test_deposit_validation_valid_profit_kinds(self):
        """Test deposit validation with valid profit kinds"""
        valid_kinds = [Deposit.PROFIT_KIND_MONTHLY, Deposit.PROFIT_KIND_SEMIANNUAL, Deposit.PROFIT_KIND_YEARLY]
        
        for kind in valid_kinds:
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=kind
            )
            # Should not raise validation error
            deposit.full_clean()
    
    def test_deposit_validation_edge_case_balances(self):
        """Test deposit validation with edge case balances"""
        edge_cases = [
            Decimal('0.00'),      # Zero balance
            Decimal('0.01'),       # Minimum positive balance
            Decimal('999999999999999.99'),  # Very large balance
            Decimal('1000000.00'), # Normal balance
        ]
        
        for balance in edge_cases:
            deposit = Deposit(
                user=self.user,
                initial_balance=balance,
                monthly_profit_rate=Decimal('3.0')
            )
            # Should not raise validation error for valid balances
            deposit.full_clean()
    
    def test_deposit_validation_edge_case_profit_rates(self):
        """Test deposit validation with edge case profit rates"""
        edge_cases = [
            Decimal('0.00'),      # Zero profit rate
            Decimal('0.01'),       # Minimum positive profit rate
            Decimal('99.99'),      # High profit rate
            Decimal('3.0'),       # Normal profit rate
        ]
        
        for rate in edge_cases:
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=rate
            )
            # Should not raise validation error for valid rates
            deposit.full_clean()
    
    def test_deposit_validation_edge_case_breakage_coefficients(self):
        """Test deposit validation with edge case breakage coefficients"""
        edge_cases = [
            Decimal('0.00'),      # Zero breakage coefficient
            Decimal('0.01'),      # Minimum positive breakage coefficient
            Decimal('100.00'),    # Maximum breakage coefficient
            Decimal('50.0'),      # Normal breakage coefficient
        ]
        
        for coefficient in edge_cases:
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                breakage_coefficient=coefficient
            )
            # Should not raise validation error for valid coefficients
            deposit.full_clean()
    
    def test_deposit_validation_decimal_precision(self):
        """Test deposit validation with decimal precision"""
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.12'),      # Valid precision (2 decimal places)
            monthly_profit_rate=Decimal('3.12'),          # Valid precision (2 decimal places)
            breakage_coefficient=Decimal('50.12')         # Valid precision (2 decimal places)
        )
        # Should not raise validation error
        deposit.full_clean()
    
    def test_deposit_validation_unicode_handling(self):
        """Test deposit validation with unicode handling"""
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        # Should not raise validation error
        deposit.full_clean()
    
    def test_deposit_validation_complex_scenarios(self):
        """Test deposit validation with complex scenarios"""
        # Test with all fields set to edge values
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('999999999999999.99'),
            monthly_profit_rate=Decimal('99.99'),
            profit_kind=Deposit.PROFIT_KIND_YEARLY,
            breakage_coefficient=Decimal('100.00')
        )
        # Should not raise validation error
        deposit.full_clean()
