"""
Test Configuration for Finance Application

This file contains common test configurations and utilities.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from finance.models import User, Account, Deposit, Transaction, AccountDailyBalance


class FinanceTestCase(TestCase):
    """Base test case for finance tests with common utilities"""
    
    def create_test_user(self, username='testuser', email='test@example.com'):
        """Create a test user with default base account"""
        return User.objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
    
    def create_test_account(self, user, name='Test Account', account_type=Account.ACCOUNT_TYPE_RIAL, 
                           initial_balance=Decimal('1000000.00'), monthly_profit_rate=Decimal('2.5')):
        """Create a test account"""
        return Account.objects.create(
            user=user,
            name=name,
            account_type=account_type,
            initial_balance=initial_balance,
            monthly_profit_rate=monthly_profit_rate
        )
    
    def create_test_deposit(self, user, initial_balance=Decimal('500000.00'), 
                           monthly_profit_rate=Decimal('3.0')):
        """Create a test deposit"""
        return Deposit.objects.create(
            user=user,
            initial_balance=initial_balance,
            monthly_profit_rate=monthly_profit_rate
        )
    
    def create_daily_snapshots(self, account, days=30, base_balance=Decimal('1000000.00')):
        """Create daily snapshots for an account"""
        today = date.today()
        for i in range(days):
            snapshot_date = today - timedelta(days=days-1-i)
            AccountDailyBalance.objects.create(
                account=account,
                snapshot_date=snapshot_date,
                balance=base_balance
            )
    
    def get_user_base_account(self, user):
        """Get user's base account (حساب پایه)"""
        return user.accounts.filter(name='حساب پایه').first()
    
    def assert_profit_transaction_created(self, user, kind, amount=None):
        """Assert that a profit transaction was created"""
        transactions = Transaction.objects.filter(
            user=user,
            kind=kind,
            applied=True
        )
        self.assertGreater(transactions.count(), 0)
        
        if amount is not None:
            total_amount = sum(txn.amount for txn in transactions)
            self.assertEqual(total_amount, amount)
        
        return transactions.first()
    
    def assert_account_balance_increased(self, account, expected_increase):
        """Assert that account balance increased by expected amount"""
        # This would need to be called before and after profit calculation
        # Implementation depends on specific test needs
        pass


# Test data constants
TEST_DATA = {
    'user1': {
        'username': 'user1',
        'email': 'user1@example.com'
    },
    'user2': {
        'username': 'user2', 
        'email': 'user2@example.com'
    },
    'rial_account': {
        'name': 'Test Rial Account',
        'account_type': Account.ACCOUNT_TYPE_RIAL,
        'initial_balance': Decimal('2000000.00'),
        'monthly_profit_rate': Decimal('3.0')
    },
    'gold_account': {
        'name': 'Test Gold Account',
        'account_type': Account.ACCOUNT_TYPE_GOLD,
        'initial_balance': Decimal('20.00'),
        'monthly_profit_rate': Decimal('1.5')
    },
    'deposit': {
        'initial_balance': Decimal('1000000.00'),
        'monthly_profit_rate': Decimal('4.0')
    }
}
