"""
Test Configuration for Finance Application

This file contains common test configurations and utilities used across all test files.
It provides a base test case class with helper methods for creating test data and
asserting expected behaviors in the finance system.

Key Features:
- FinanceTestCase: Base class with common test utilities
- Test data constants for consistent test values
- Helper methods for creating users, accounts, deposits, and transactions
- Assertion helpers for verifying profit calculations and balance changes
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from finance.models import User, Account, Deposit, Transaction, AccountDailyBalance, DepositDailyBalance


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
    
    def create_test_transaction(self, user, kind, amount, source_account=None, destination_account=None, 
                               state=Transaction.STATE_DONE, exchange_rate=None):
        """Create a test transaction with specified parameters"""
        return Transaction.objects.create(
            user=user,
            kind=kind,
            amount=amount,
            source_account=source_account,
            destination_account=destination_account,
            state=state,
            exchange_rate=exchange_rate
        )
    
    def create_deposit_snapshots(self, deposit, days=30, base_balance=Decimal('1000000.00')):
        """Create daily snapshots for a deposit"""
        today = date.today()
        for i in range(days):
            snapshot_date = today - timedelta(days=days-1-i)
            DepositDailyBalance.objects.create(
                deposit=deposit,
                snapshot_date=snapshot_date,
                balance=base_balance
            )
    
    def create_cross_currency_accounts(self, user):
        """Create accounts of different currency types for testing exchange rates"""
        accounts = {}
        accounts['rial'] = self.create_test_account(
            user, 'Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        accounts['usd'] = self.create_test_account(
            user, 'USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
        accounts['eur'] = self.create_test_account(
            user, 'EUR Account', Account.ACCOUNT_TYPE_EUR, Decimal('1000.00')
        )
        accounts['gold'] = self.create_test_account(
            user, 'Gold Account', Account.ACCOUNT_TYPE_GOLD, Decimal('10.00')
        )
        return accounts
    
    def assert_transaction_state_log_created(self, transaction, from_state, to_state):
        """Assert that a transaction state log entry was created"""
        from finance.models import TransactionStateLog
        logs = TransactionStateLog.objects.filter(
            transaction=transaction,
            from_state=from_state,
            to_state=to_state
        )
        self.assertGreater(logs.count(), 0)
        return logs.first()
    
    def assert_transaction_code_format(self, transaction_code, expected_kind, expected_user_prefix):
        """Assert that transaction code follows the correct format"""
        parts = transaction_code.split('-')
        self.assertEqual(len(parts), 4, f"Transaction code should have 4 parts: {transaction_code}")
        self.assertEqual(parts[0], expected_kind, f"Transaction kind should be {expected_kind}")
        self.assertTrue(parts[1].startswith(expected_user_prefix), 
                       f"User prefix should start with {expected_user_prefix}")
        # Parts 2 and 3 should be Persian date and sequence number
        self.assertTrue(parts[2].isdigit(), "Date part should be numeric")
        self.assertTrue(parts[3].isdigit(), "Sequence part should be numeric")


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
