"""
Comprehensive Account Balance Tests

This test file focuses on improving coverage for the Account.balance property,
which is critical for financial accuracy.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from finance.models import User, Account, Transaction
from finance.tests.test_config import FinanceTestCase


class AccountBalanceComprehensiveTests(FinanceTestCase):
    """Comprehensive tests for Account balance calculation to improve coverage"""
    
    def setUp(self):
        """Set up test data"""
        self.user = self.create_test_user()
        self.rial_account = self.create_test_account(
            self.user, 
            name='Test Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000000.00')
        )
        self.gold_account = self.create_test_account(
            self.user,
            name='Test Gold Account', 
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('10.00')
        )

    def test_balance_initial_only(self):
        """Test balance calculation with only initial balance"""
        # No transactions, should return initial balance
        self.assertEqual(self.rial_account.balance, Decimal('1000000.00'))
        self.assertEqual(self.gold_account.balance, Decimal('10.00'))

    def test_balance_credit_increase(self):
        """Test balance with credit increase transactions"""
        # Create credit increase transaction
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('200000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Balance should be initial + credit increase
        expected_balance = Decimal('1000000.00') + Decimal('200000.00')
        self.assertEqual(self.rial_account.balance, expected_balance)

    def test_balance_profit_deposit_to_account(self):
        """Test balance with profit deposit to account transactions"""
        # Create profit deposit transaction
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('50000.00'),
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Balance should be initial + profit
        expected_balance = Decimal('1000000.00') + Decimal('50000.00')
        self.assertEqual(self.rial_account.balance, expected_balance)

    def test_balance_profit_account(self):
        """Test balance with profit account transactions"""
        # Create profit account transaction
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('30000.00'),
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Balance should be initial + profit
        expected_balance = Decimal('1000000.00') + Decimal('30000.00')
        self.assertEqual(self.rial_account.balance, expected_balance)

    def test_balance_account_to_account_same_currency(self):
        """Test balance with account-to-account transfer (same currency)"""
        # Create transfer from gold to rial (same currency logic)
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.gold_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Rial account should decrease
        expected_rial_balance = Decimal('1000000.00') - Decimal('100000.00')
        self.assertEqual(self.rial_account.balance, expected_rial_balance)
        
        # Gold account should increase
        expected_gold_balance = Decimal('10.00') + Decimal('100000.00')
        self.assertEqual(self.gold_account.balance, expected_gold_balance)

    def test_balance_account_to_account_cross_currency(self):
        """Test balance with cross-currency transfer using exchange rate"""
        # Create cross-currency transfer with exchange rate
        # Rial → Gold: amount / exchange_rate (since exchange_rate = rials per gold)
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.gold_account,
            amount=Decimal('100000.00'),  # Amount in rial
            exchange_rate=Decimal('1000.0'),  # 1 gold = 1000 rial (exchange_rate = rials per gold)
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Rial account should decrease by full amount
        expected_rial_balance = Decimal('1000000.00') - Decimal('100000.00')
        self.assertEqual(self.rial_account.balance, expected_rial_balance)
        
        # Gold account should increase by converted amount (rial / exchange_rate)
        converted_amount = Decimal('100000.00') / Decimal('1000.0')  # 100000 rial / 1000 rial/gold = 100 gold
        expected_gold_balance = Decimal('10.00') + converted_amount
        self.assertEqual(self.gold_account.balance, expected_gold_balance)

    def test_balance_account_to_account_cross_currency_reverse(self):
        """Test balance with cross-currency transfer in reverse direction (Gold → Rial)"""
        # Create cross-currency transfer in reverse direction
        # Gold → Rial: amount * exchange_rate (since exchange_rate = rials per gold)
        Transaction.objects.create(
            user=self.user,
            source_account=self.gold_account,
            destination_account=self.rial_account,
            amount=Decimal('5.00'),  # Amount in gold
            exchange_rate=Decimal('1000.0'),  # 1 gold = 1000 rial (exchange_rate = rials per gold)
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Gold account should decrease by full amount
        expected_gold_balance = Decimal('10.00') - Decimal('5.00')
        self.assertEqual(self.gold_account.balance, expected_gold_balance)
        
        # Rial account should increase by converted amount (gold * exchange_rate)
        converted_amount = Decimal('5.00') * Decimal('1000.0')  # 5 gold * 1000 rial/gold = 5000 rial
        expected_rial_balance = Decimal('1000000.00') + converted_amount
        self.assertEqual(self.rial_account.balance, expected_rial_balance)

    def test_balance_account_to_account_no_exchange_rate(self):
        """Test balance with account-to-account transfer without exchange rate"""
        # Create transfer without exchange rate (same currency)
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.gold_account,
            amount=Decimal('50000.00'),
            exchange_rate=None,
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Should use amount directly (no conversion)
        expected_rial_balance = Decimal('1000000.00') - Decimal('50000.00')
        self.assertEqual(self.rial_account.balance, expected_rial_balance)
        
        expected_gold_balance = Decimal('10.00') + Decimal('50000.00')
        self.assertEqual(self.gold_account.balance, expected_gold_balance)

    def test_balance_multiple_transactions(self):
        """Test balance with multiple different transaction types"""
        # Create multiple transactions
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('25000.00'),
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('15000.00'),
            kind=Transaction.KIND_PROFIT_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Calculate expected balance
        expected_balance = (Decimal('1000000.00') + 
                           Decimal('100000.00') + 
                           Decimal('25000.00') + 
                           Decimal('15000.00'))
        self.assertEqual(self.rial_account.balance, expected_balance)

    def test_balance_ignores_unapplied_transactions(self):
        """Test that unapplied transactions don't affect balance"""
        # Create transaction in waiting state (not done, so it won't be auto-applied)
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('200000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_WAITING_TREASURY,  # Not done state
            applied=False  # Not applied
        )
        
        # Balance should remain initial (unapplied transaction ignored)
        self.assertEqual(self.rial_account.balance, Decimal('1000000.00'))

    def test_balance_ignores_pending_transactions(self):
        """Test that non-DONE state transactions don't affect balance"""
        # Create transaction in waiting state but not applied
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('200000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_WAITING_TREASURY,
            applied=False  # Not applied
        )
        
        # Balance should remain initial (non-applied transaction ignored)
        self.assertEqual(self.rial_account.balance, Decimal('1000000.00'))

    def test_balance_outgoing_transactions(self):
        """Test balance calculation with outgoing transactions"""
        # Create outgoing transaction (source account)
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.gold_account,
            amount=Decimal('300000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Rial account should decrease
        expected_balance = Decimal('1000000.00') - Decimal('300000.00')
        self.assertEqual(self.rial_account.balance, expected_balance)

    def test_balance_complex_scenario(self):
        """Test balance with complex mix of transactions"""
        # Multiple incoming transactions
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('50000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('30000.00'),
            kind=Transaction.KIND_PROFIT_DEPOSIT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Outgoing transaction
        Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=self.gold_account,
            amount=Decimal('20000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Calculate expected balance
        expected_balance = (Decimal('1000000.00') +  # Initial
                           Decimal('50000.00') +      # Credit increase
                           Decimal('30000.00') -      # Profit deposit
                           Decimal('20000.00'))       # Transfer out
        self.assertEqual(self.rial_account.balance, expected_balance)

    def test_balance_zero_initial(self):
        """Test balance calculation with zero initial balance"""
        # Create account with zero initial balance
        zero_account = Account.objects.create(
            user=self.user,
            name='Zero Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('0.00')
        )
        
        # Add some transactions
        Transaction.objects.create(
            user=self.user,
            destination_account=zero_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Balance should be transaction amount only
        self.assertEqual(zero_account.balance, Decimal('100000.00'))

    def test_balance_negative_transactions(self):
        """Test balance with negative amount transactions"""
        # Create transaction with negative amount (should be handled properly)
        Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('-50000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE,
            applied=True
        )
        
        # Balance should be initial + negative amount
        expected_balance = Decimal('1000000.00') + Decimal('-50000.00')
        self.assertEqual(self.rial_account.balance, expected_balance)
