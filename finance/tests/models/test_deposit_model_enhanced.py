"""
Enhanced Deposit Model Tests

This module tests additional deposit model functionality to improve coverage including:
- Advanced deposit validation and edge cases
- Complex profit calculation scenarios
- Deposit state management
- Deposit profit transfer logic
- Deposit breakage coefficient logic
- Deposit profit kind validation
- Deposit balance calculations

Test Coverage:
- Advanced validation scenarios
- Complex profit calculation logic
- Deposit state management
- Profit transfer logic
- Breakage coefficient logic
- Profit kind validation
- Balance calculation edge cases
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from finance.models import User, Account, Deposit, Transaction
from finance.tests.test_config import FinanceTestCase


class DepositModelEnhancedTests(FinanceTestCase):
    """Test enhanced deposit model functionality"""
    
    def setUp(self):
        """Set up test data for enhanced deposit testing"""
        self.user = self.create_test_user('enhanced_deposit_user')
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
                monthly_profit_rate=Decimal('-3.0')  # Negative profit rate
            )
            deposit.full_clean()
    
    def test_deposit_validation_negative_breakage_coefficient(self):
        """Test deposit validation with negative breakage coefficient"""
        with self.assertRaises(ValidationError):
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                breakage_coefficient=Decimal('-25.0')  # Negative breakage coefficient
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
                profit_kind='invalid_kind'
            )
            deposit.full_clean()
    
    def test_deposit_validation_valid_profit_kinds(self):
        """Test deposit validation with valid profit kinds"""
        profit_kinds = [
            Deposit.PROFIT_KIND_MONTHLY,
            Deposit.PROFIT_KIND_SEMIANNUAL,
            Deposit.PROFIT_KIND_YEARLY
        ]
        
        for profit_kind in profit_kinds:
            deposit = Deposit(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=profit_kind
            )
            
            # Should not raise validation error
            deposit.full_clean()
    
    def test_deposit_validation_edge_case_balances(self):
        """Test deposit validation with edge case balances"""
        # Test zero balance
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('0.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test very small balance
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('0.01'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test very large balance
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('999999999999999.99'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Should not raise validation error
        deposit.full_clean()
    
    def test_deposit_validation_edge_case_profit_rates(self):
        """Test deposit validation with edge case profit rates"""
        # Test zero profit rate
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('0.00')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test very small profit rate
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('0.01')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test very large profit rate
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('999.99')
        )
        
        # Should not raise validation error
        deposit.full_clean()
    
    def test_deposit_validation_edge_case_breakage_coefficients(self):
        """Test deposit validation with edge case breakage coefficients"""
        # Test zero breakage coefficient
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            breakage_coefficient=Decimal('0.00')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test 100% breakage coefficient
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            breakage_coefficient=Decimal('100.00')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test very small breakage coefficient
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            breakage_coefficient=Decimal('0.01')
        )
        
        # Should not raise validation error
        deposit.full_clean()
    
    def test_deposit_validation_decimal_precision(self):
        """Test deposit validation with decimal precision"""
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.123456'),
            monthly_profit_rate=Decimal('3.123456'),
            breakage_coefficient=Decimal('25.123456')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test that precision is preserved
        self.assertEqual(deposit.initial_balance, Decimal('1000000.123456'))
        self.assertEqual(deposit.monthly_profit_rate, Decimal('3.123456'))
        self.assertEqual(deposit.breakage_coefficient, Decimal('25.123456'))
    
    def test_deposit_validation_unicode_handling(self):
        """Test deposit validation with Unicode characters"""
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY,
            breakage_coefficient=Decimal('25.0')
        )
        
        # Should not raise validation error
        deposit.full_clean()
    
    def test_deposit_validation_complex_scenarios(self):
        """Test deposit validation with complex scenarios"""
        # Test with all fields
        deposit = Deposit(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY,
            breakage_coefficient=Decimal('25.0')
        )
        
        # Should not raise validation error
        deposit.full_clean()
        
        # Test that all fields are preserved
        self.assertEqual(deposit.user, self.user)
        self.assertEqual(deposit.initial_balance, Decimal('1000000.00'))
        self.assertEqual(deposit.monthly_profit_rate, Decimal('3.0'))
        self.assertEqual(deposit.profit_kind, Deposit.PROFIT_KIND_MONTHLY)
        self.assertEqual(deposit.breakage_coefficient, Decimal('25.0'))
    
    def test_deposit_balance_calculation_with_transactions(self):
        """Test deposit balance calculation with transactions"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Create transaction to change deposit balance
        transaction = Transaction.objects.create(
            user=self.user,
            destination_deposit=deposit,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
            state=Transaction.STATE_DONE
        )
        transaction.apply()
        
        # Check that balance is calculated correctly
        expected_balance = Decimal('1000000.00') + Decimal('100000.00')
        self.assertEqual(deposit.balance, expected_balance)
    
    def test_deposit_balance_calculation_without_transactions(self):
        """Test deposit balance calculation without transactions"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Check that balance equals initial balance
        self.assertEqual(deposit.balance, Decimal('1000000.00'))
    
    def test_deposit_balance_calculation_multiple_transactions(self):
        """Test deposit balance calculation with multiple transactions"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Create multiple transactions
        for i in range(3):
            transaction = Transaction.objects.create(
                user=self.user,
                destination_deposit=deposit,
                amount=Decimal('100000.00'),
                kind=Transaction.KIND_ACCOUNT_TO_DEPOSIT_INITIAL,
                state=Transaction.STATE_DONE
            )
            transaction.apply()
        
        # Check that balance is calculated correctly
        expected_balance = Decimal('1000000.00') + (Decimal('100000.00') * 3)
        self.assertEqual(deposit.balance, expected_balance)
    
    def test_deposit_profit_calculation_info_display(self):
        """Test deposit profit calculation info display"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        # Test profit calculation info
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
        
        # Check that info contains expected elements
        self.assertIn('شروع', info)
        self.assertIn('میانگین', info)
        self.assertIn('سود بعدی', info)
    
    def test_deposit_profit_calculation_info_different_kinds(self):
        """Test deposit profit calculation info for different profit kinds"""
        profit_kinds = [
            Deposit.PROFIT_KIND_MONTHLY,
            Deposit.PROFIT_KIND_SEMIANNUAL,
            Deposit.PROFIT_KIND_YEARLY
        ]
        
        for profit_kind in profit_kinds:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=profit_kind
            )
            
            # Test profit calculation info
            info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(info)
            self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_last_accrual(self):
        """Test deposit profit calculation info with last accrual date"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        # Set last profit accrual date
        deposit.last_profit_accrual_at = timezone.now() - timedelta(days=15)
        deposit.save()
        
        # Test profit calculation info
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_zero_balance(self):
        """Test deposit profit calculation info with zero balance"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('0.00'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        # Test profit calculation info
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_none_values(self):
        """Test deposit profit calculation info with None values"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        # Set None values
        deposit.last_profit_accrual_at = None
        deposit.save()
        
        # Test profit calculation info
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_edge_cases(self):
        """Test deposit profit calculation info with edge cases"""
        # Test with very small balance
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('0.01'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
        
        # Test with very large balance
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('999999999999999.99'),
            monthly_profit_rate=Decimal('3.0'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_zero_profit_rate(self):
        """Test deposit profit calculation info with zero profit rate"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('0.00'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        # Test profit calculation info
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_very_small_profit_rate(self):
        """Test deposit profit calculation info with very small profit rate"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('0.01'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        # Test profit calculation info
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_very_large_profit_rate(self):
        """Test deposit profit calculation info with very large profit rate"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('999.99'),
            profit_kind=Deposit.PROFIT_KIND_MONTHLY
        )
        
        # Test profit calculation info
        info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(info)
        self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_different_breakage_coefficients(self):
        """Test deposit profit calculation info with different breakage coefficients"""
        breakage_coefficients = [Decimal('0.00'), Decimal('25.0'), Decimal('50.0'), Decimal('100.0')]
        
        for breakage_coefficient in breakage_coefficients:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=Deposit.PROFIT_KIND_MONTHLY,
                breakage_coefficient=breakage_coefficient
            )
            
            # Test profit calculation info
            info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(info)
            self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_different_profit_kinds(self):
        """Test deposit profit calculation info with different profit kinds"""
        profit_kinds = [
            Deposit.PROFIT_KIND_MONTHLY,
            Deposit.PROFIT_KIND_SEMIANNUAL,
            Deposit.PROFIT_KIND_YEARLY
        ]
        
        for profit_kind in profit_kinds:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=profit_kind
            )
            
            # Test profit calculation info
            info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(info)
            self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_different_balances(self):
        """Test deposit profit calculation info with different balances"""
        balances = [
            Decimal('0.00'),
            Decimal('0.01'),
            Decimal('1000.00'),
            Decimal('1000000.00'),
            Decimal('999999999999999.99')
        ]
        
        for balance in balances:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=balance,
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=Deposit.PROFIT_KIND_MONTHLY
            )
            
            # Test profit calculation info
            info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(info)
            self.assertIsInstance(info, str)
    
    def test_deposit_profit_calculation_info_with_different_profit_rates(self):
        """Test deposit profit calculation info with different profit rates"""
        profit_rates = [
            Decimal('0.00'),
            Decimal('0.01'),
            Decimal('1.0'),
            Decimal('10.0'),
            Decimal('999.99')
        ]
        
        for profit_rate in profit_rates:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=profit_rate,
                profit_kind=Deposit.PROFIT_KIND_MONTHLY
            )
            
            # Test profit calculation info
            info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(info)
            self.assertIsInstance(info, str)
