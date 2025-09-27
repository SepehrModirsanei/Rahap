"""
Deposit Profit Information Tests

This module tests deposit profit calculation information display including:
- Profit calculation info display
- Different profit kinds
- Last accrual handling
- Zero balance scenarios
- None values handling
- Edge cases and boundary conditions
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from finance.models import User, Account, Deposit
from finance.tests.test_config import FinanceTestCase


class DepositProfitInfoTests(FinanceTestCase):
    """Test deposit profit calculation information functionality"""
    
    def setUp(self):
        """Set up test data for deposit profit info testing"""
        self.user = self.create_test_user('deposit_profit_info_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
    
    def test_deposit_profit_calculation_info_display(self):
        """Test deposit profit calculation info display"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        # Test profit calculation info
        profit_info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(profit_info)
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_different_kinds(self):
        """Test deposit profit calculation info with different profit kinds"""
        kinds = [Deposit.PROFIT_KIND_MONTHLY, Deposit.PROFIT_KIND_SEMIANNUAL, Deposit.PROFIT_KIND_YEARLY]
        
        for kind in kinds:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=kind
            )
            
            profit_info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(profit_info)
            self.assertIn('profit_rate', profit_info)
            self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_last_accrual(self):
        """Test deposit profit calculation info with last accrual date"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            last_profit_accrual_at=timezone.now() - timedelta(days=15)
        )
        
        profit_info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(profit_info)
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_zero_balance(self):
        """Test deposit profit calculation info with zero balance"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('0.00'),
            monthly_profit_rate=Decimal('3.0')
        )
        
        profit_info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(profit_info)
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_none_values(self):
        """Test deposit profit calculation info with none values"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('3.0'),
            last_profit_accrual_at=None
        )
        
        profit_info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(profit_info)
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_edge_cases(self):
        """Test deposit profit calculation info with edge cases"""
        edge_cases = [
            {'balance': Decimal('0.01'), 'rate': Decimal('0.01')},
            {'balance': Decimal('999999999999999.99'), 'rate': Decimal('99.99')},
            {'balance': Decimal('1000000.00'), 'rate': Decimal('3.0')},
        ]
        
        for case in edge_cases:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=case['balance'],
                monthly_profit_rate=case['rate']
            )
            
            profit_info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(profit_info)
            self.assertIn('profit_rate', profit_info)
            self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_zero_profit_rate(self):
        """Test deposit profit calculation info with zero profit rate"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('0.00')
        )
        
        profit_info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(profit_info)
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_very_small_profit_rate(self):
        """Test deposit profit calculation info with very small profit rate"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('0.01')
        )
        
        profit_info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(profit_info)
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_very_large_profit_rate(self):
        """Test deposit profit calculation info with very large profit rate"""
        deposit = Deposit.objects.create(
            user=self.user,
            initial_balance=Decimal('1000000.00'),
            monthly_profit_rate=Decimal('99.99')
        )
        
        profit_info = deposit.get_profit_calculation_info()
        self.assertIsNotNone(profit_info)
        self.assertIn('profit_rate', profit_info)
        self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_different_breakage_coefficients(self):
        """Test deposit profit calculation info with different breakage coefficients"""
        coefficients = [Decimal('0.00'), Decimal('25.00'), Decimal('50.00'), Decimal('100.00')]
        
        for coefficient in coefficients:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                breakage_coefficient=coefficient
            )
            
            profit_info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(profit_info)
            self.assertIn('profit_rate', profit_info)
            self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_different_profit_kinds(self):
        """Test deposit profit calculation info with different profit kinds"""
        kinds = [Deposit.PROFIT_KIND_MONTHLY, Deposit.PROFIT_KIND_SEMIANNUAL, Deposit.PROFIT_KIND_YEARLY]
        
        for kind in kinds:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=Decimal('3.0'),
                profit_kind=kind
            )
            
            profit_info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(profit_info)
            self.assertIn('profit_rate', profit_info)
            self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_different_balances(self):
        """Test deposit profit calculation info with different balances"""
        balances = [Decimal('0.00'), Decimal('1000.00'), Decimal('1000000.00'), Decimal('999999999999999.99')]
        
        for balance in balances:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=balance,
                monthly_profit_rate=Decimal('3.0')
            )
            
            profit_info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(profit_info)
            self.assertIn('profit_rate', profit_info)
            self.assertIn('next_transfer_date', profit_info)
    
    def test_deposit_profit_calculation_info_with_different_profit_rates(self):
        """Test deposit profit calculation info with different profit rates"""
        rates = [Decimal('0.00'), Decimal('0.01'), Decimal('3.0'), Decimal('99.99')]
        
        for rate in rates:
            deposit = Deposit.objects.create(
                user=self.user,
                initial_balance=Decimal('1000000.00'),
                monthly_profit_rate=rate
            )
            
            profit_info = deposit.get_profit_calculation_info()
            self.assertIsNotNone(profit_info)
            self.assertIn('profit_rate', profit_info)
            self.assertIn('next_transfer_date', profit_info)
