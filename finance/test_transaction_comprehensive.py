from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Wallet, Account, Deposit, Transaction


class TransactionFormTests(TestCase):
    """Comprehensive tests for transaction forms and edge cases"""
    
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='userpass1'
        )
        cls.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='userpass2'
        )
        # Wallets are auto-created via signal
        
        # Ensure wallets exist and fund user1's wallet
        if not hasattr(cls.user1, 'wallet'):
            Wallet.objects.create(user=cls.user1)
        if not hasattr(cls.user2, 'wallet'):
            Wallet.objects.create(user=cls.user2)
            
        cls.user1.wallet.balance = Decimal('1000.00')
        cls.user1.wallet.save()
        
        # Create accounts for user1
        cls.rial_account = Account.objects.create(
            user=cls.user1,
            wallet=cls.user1.wallet,
            name='Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            balance=Decimal('500.00'),
            monthly_profit_rate=Decimal('2.5')
        )
        
        cls.usd_account = Account.objects.create(
            user=cls.user1,
            wallet=cls.user1.wallet,
            name='USD Account',
            account_type=Account.ACCOUNT_TYPE_FOREIGN,
            balance=Decimal('100.00'),
            monthly_profit_rate=Decimal('1.0')
        )
        
        cls.gold_account = Account.objects.create(
            user=cls.user1,
            wallet=cls.user1.wallet,
            name='Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            balance=Decimal('10.50'),
            monthly_profit_rate=Decimal('0.5')
        )

    def setUp(self):
        # Ensure wallets exist and reset balances before each test
        if not hasattr(self.user1, 'wallet'):
            Wallet.objects.create(user=self.user1)
        if not hasattr(self.user2, 'wallet'):
            Wallet.objects.create(user=self.user2)
            
        self.user1.wallet.balance = Decimal('1000.00')
        self.user1.wallet.save()
        self.rial_account.balance = Decimal('500.00')
        self.rial_account.save()
        self.usd_account.balance = Decimal('100.00')
        self.usd_account.save()
        self.gold_account.balance = Decimal('10.50')
        self.gold_account.save()

    # ==================== BASIC TRANSACTION TESTS ====================
    
    def test_add_to_wallet_transaction(self):
        """Test adding money to wallet"""
        txn = Transaction.objects.create(
            user=self.user1,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_ADD_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1100.00'))
        self.assertTrue(txn.applied)

    def test_remove_from_wallet_transaction(self):
        """Test removing money from wallet"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_wallet=self.user1.wallet,
            amount=Decimal('200.00'),
            kind=Transaction.KIND_REMOVE_FROM_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('800.00'))
        self.assertTrue(txn.applied)

    def test_wallet_to_wallet_transfer(self):
        """Test transferring between wallets"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_wallet=self.user1.wallet,
            destination_wallet=self.user2.wallet,
            amount=Decimal('150.00'),
            kind=Transaction.KIND_TRANSFER_WALLET_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.user1.wallet.refresh_from_db()
        self.user2.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('850.00'))
        self.assertEqual(self.user2.wallet.balance, Decimal('150.00'))
        self.assertTrue(txn.applied)

    def test_account_to_wallet_transfer_rial(self):
        """Test transferring from rial account to wallet"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.rial_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.rial_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.rial_account.balance, Decimal('400.00'))
        self.assertEqual(self.user1.wallet.balance, Decimal('1100.00'))
        self.assertTrue(txn.applied)

    def test_wallet_to_account_transfer_rial(self):
        """Test transferring from wallet to rial account"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_wallet=self.user1.wallet,
            destination_account=self.rial_account,
            amount=Decimal('50.00'),
            kind=Transaction.KIND_TRANSFER_WALLET_TO_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.rial_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.rial_account.balance, Decimal('550.00'))
        self.assertEqual(self.user1.wallet.balance, Decimal('950.00'))
        self.assertTrue(txn.applied)

    # ==================== EXCHANGE RATE TESTS ====================
    
    def test_foreign_account_to_wallet_with_exchange_rate(self):
        """Test converting foreign currency to wallet with exchange rate"""
        # USD to IRR: 1 USD = 500,000 IRR
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('1.00'),  # 1 USD
            exchange_rate=Decimal('500000.00'),  # 500,000 IRR per USD
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.usd_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.usd_account.balance, Decimal('99.00'))  # 100 - 1
        self.assertEqual(self.user1.wallet.balance, Decimal('501000.00'))  # 1000 + (1 * 500000)
        self.assertTrue(txn.applied)

    def test_wallet_to_foreign_account_with_exchange_rate(self):
        """Test converting wallet to foreign currency with exchange rate"""
        # IRR to USD: 500,000 IRR = 1 USD
        txn = Transaction.objects.create(
            user=self.user1,
            source_wallet=self.user1.wallet,
            destination_account=self.usd_account,
            amount=Decimal('1000.00'),  # 1000 IRR from wallet
            exchange_rate=Decimal('500000.00'),  # 500,000 IRR per USD
            kind=Transaction.KIND_TRANSFER_WALLET_TO_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.usd_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.usd_account.balance, Decimal('100.002'))  # 100 + (1000/500000)
        self.assertEqual(self.user1.wallet.balance, Decimal('0.00'))  # 1000 - 1000 (amount is deducted from source)
        self.assertTrue(txn.applied)

    def test_gold_account_to_wallet_with_exchange_rate(self):
        """Test converting gold to wallet with exchange rate"""
        # Gold to IRR: 1 gram = 2,000,000 IRR
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.gold_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('0.5'),  # 0.5 grams
            exchange_rate=Decimal('2000000.00'),  # 2,000,000 IRR per gram
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.gold_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.gold_account.balance, Decimal('10.00'))  # 10.5 - 0.5
        self.assertEqual(self.user1.wallet.balance, Decimal('1001000.00'))  # 1000 + (0.5 * 2000000)
        self.assertTrue(txn.applied)

    # ==================== EXCHANGE RATE EDGE CASES ====================
    
    def test_exchange_rate_zero_validation(self):
        """Test that zero exchange rate is rejected"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('1.00'),
            exchange_rate=Decimal('0.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Exchange rate must be positive', str(cm.exception))

    def test_exchange_rate_negative_validation(self):
        """Test that negative exchange rate is rejected"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('1.00'),
            exchange_rate=Decimal('-100.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Exchange rate must be positive', str(cm.exception))

    def test_exchange_rate_too_large_validation(self):
        """Test that extremely large exchange rate is rejected"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('1.00'),
            exchange_rate=Decimal('1000000000000.00'),  # Too large
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Exchange rate is too large', str(cm.exception))

    def test_exchange_rate_too_small_validation(self):
        """Test that extremely small exchange rate is rejected"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('1.00'),
            exchange_rate=Decimal('0.0000001'),  # Too small
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Exchange rate is too small', str(cm.exception))

    def test_very_small_exchange_rate_precision(self):
        """Test exchange rate with very small values (precision edge case)"""
        # Very small exchange rate: 1 unit = 0.000001 IRR
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('10.00'),  # 10 units (within available balance)
            exchange_rate=Decimal('0.000001'),  # Minimum allowed rate
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.usd_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.usd_account.balance, Decimal('90.00'))  # 100 - 10
        self.assertEqual(self.user1.wallet.balance, Decimal('1000.000010'))  # 1000 + (10 * 0.000001)
        self.assertTrue(txn.applied)

    def test_very_large_exchange_rate_precision(self):
        """Test exchange rate with very large values (precision edge case)"""
        # Very large exchange rate: 1 unit = 999,999,999,999.999999 IRR
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('0.000001'),  # Very small amount
            exchange_rate=Decimal('1000000.00'),  # Large but reasonable rate
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.usd_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.usd_account.balance, Decimal('99.999999'))  # 100 - 0.000001
        self.assertEqual(self.user1.wallet.balance, Decimal('1001.00'))  # 1000 + (0.000001 * 1000000)
        self.assertTrue(txn.applied)

    def test_division_by_zero_protection(self):
        """Test that division by zero is prevented during application"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_wallet=self.user1.wallet,
            destination_account=self.usd_account,
            amount=Decimal('100.00'),
            exchange_rate=Decimal('0.00'),  # This should be caught in clean()
            kind=Transaction.KIND_TRANSFER_WALLET_TO_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        
        # Should fail during clean() validation
        with self.assertRaises(ValidationError):
            txn.clean()

    # ==================== INSUFFICIENT BALANCE TESTS ====================
    
    def test_insufficient_wallet_balance_validation(self):
        """Test that insufficient wallet balance is caught"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_wallet=self.user1.wallet,
            destination_wallet=self.user2.wallet,
            amount=Decimal('1500.00'),  # More than available (1000)
            kind=Transaction.KIND_TRANSFER_WALLET_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Insufficient wallet balance', str(cm.exception))

    def test_insufficient_account_balance_validation(self):
        """Test that insufficient account balance is caught"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('150.00'),  # More than available (100)
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Insufficient account balance', str(cm.exception))

    # ==================== TRANSACTION STATE TESTS ====================
    
    def test_advance_state_method(self):
        """Test the advance_state method"""
        txn = Transaction.objects.create(
            user=self.user1,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_ADD_TO_WALLET,
            state=Transaction.STATE_WAITING_TREASURY
        )
        
        # Advance through states
        self.assertTrue(txn.advance_state())
        self.assertEqual(txn.state, Transaction.STATE_WAITING_SANDOGH)
        
        self.assertTrue(txn.advance_state())
        self.assertEqual(txn.state, Transaction.STATE_VERIFIED_KHAZANEDAR)
        
        self.assertTrue(txn.advance_state())
        self.assertEqual(txn.state, Transaction.STATE_DONE)
        
        # Cannot advance further
        self.assertFalse(txn.advance_state())
        self.assertEqual(txn.state, Transaction.STATE_DONE)

    def test_transaction_only_applies_when_done(self):
        """Test that transactions only apply when state is DONE"""
        txn = Transaction.objects.create(
            user=self.user1,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_ADD_TO_WALLET,
            state=Transaction.STATE_WAITING_TREASURY
        )
        
        txn.apply()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1000.00'))  # Unchanged
        self.assertFalse(txn.applied)

    def test_scheduled_transaction_does_not_apply_early(self):
        """Test that scheduled transactions don't apply before their time"""
        future_time = timezone.now() + timedelta(hours=1)
        txn = Transaction.objects.create(
            user=self.user1,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_ADD_TO_WALLET,
            state=Transaction.STATE_DONE,
            scheduled_for=future_time
        )
        
        txn.apply()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1000.00'))  # Unchanged
        self.assertFalse(txn.applied)

    # ==================== REVERT TESTS ====================
    
    def test_revert_add_to_wallet(self):
        """Test reverting an add to wallet transaction"""
        txn = Transaction.objects.create(
            user=self.user1,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_ADD_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1100.00'))
        
        txn.revert()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1000.00'))
        self.assertFalse(txn.applied)

    def test_revert_foreign_currency_transaction(self):
        """Test reverting a foreign currency transaction"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('1.00'),
            exchange_rate=Decimal('500000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        # Verify applied
        self.usd_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.usd_account.balance, Decimal('99.00'))
        self.assertEqual(self.user1.wallet.balance, Decimal('501000.00'))
        
        # Revert
        txn.revert()
        self.usd_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.usd_account.balance, Decimal('100.00'))
        self.assertEqual(self.user1.wallet.balance, Decimal('1000.00'))
        self.assertFalse(txn.applied)

    # ==================== DEPOSIT TRANSACTION TESTS ====================
    
    def test_wallet_to_deposit_initial(self):
        """Test initial deposit from wallet"""
        deposit = Deposit.objects.create(
            user=self.user1,
            wallet=self.user1.wallet,
            amount=Decimal('0.00'),  # Start with 0
            monthly_profit_rate=Decimal('2.0')
        )
        
        txn = Transaction.objects.create(
            user=self.user1,
            source_wallet=self.user1.wallet,
            destination_deposit=deposit,
            amount=Decimal('200.00'),
            kind=Transaction.KIND_WALLET_TO_DEPOSIT_INITIAL,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.user1.wallet.refresh_from_db()
        deposit.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('800.00'))  # 1000 - 200
        self.assertEqual(deposit.amount, Decimal('200.00'))
        self.assertTrue(txn.applied)

    # ==================== ACCOUNT TO ACCOUNT TESTS ====================
    
    def test_account_to_account_transfer_rial_to_foreign(self):
        """Test transferring from rial account to foreign account (no exchange rate conversion)"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.rial_account,
            destination_account=self.usd_account,
            amount=Decimal('500.00'),  # 500 IRR
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.rial_account.refresh_from_db()
        self.usd_account.refresh_from_db()
        self.assertEqual(self.rial_account.balance, Decimal('0.00'))  # 500 - 500
        self.assertEqual(self.usd_account.balance, Decimal('600.00'))  # 100 + 500 (no conversion)
        self.assertTrue(txn.applied)

    def test_account_to_account_transfer_foreign_to_rial(self):
        """Test transferring from foreign account to rial account (no exchange rate conversion)"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_account=self.rial_account,
            amount=Decimal('1.00'),  # 1 USD
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.rial_account.refresh_from_db()
        self.usd_account.refresh_from_db()
        self.assertEqual(self.rial_account.balance, Decimal('501.00'))  # 500 + 1 (no conversion)
        self.assertEqual(self.usd_account.balance, Decimal('99.00'))  # 100 - 1
        self.assertTrue(txn.applied)

    # ==================== EDGE CASE COMBINATIONS ====================
    
    def test_multiple_decimal_precision_handling(self):
        """Test handling of multiple decimal places in amounts and exchange rates"""
        txn = Transaction.objects.create(
            user=self.user1,
            source_account=self.usd_account,
            destination_wallet=self.user1.wallet,
            amount=Decimal('1.234567'),  # Many decimal places
            exchange_rate=Decimal('123456.789012'),  # Many decimal places
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.usd_account.refresh_from_db()
        self.user1.wallet.refresh_from_db()
        expected_credit = Decimal('1.234567') * Decimal('123456.789012')
        self.assertEqual(self.usd_account.balance, Decimal('98.765433'))  # 100 - 1.234567
        # Round to 6 decimal places to match database precision
        expected_balance = (Decimal('1000.00') + expected_credit).quantize(Decimal('0.000001'))
        actual_balance = self.user1.wallet.balance.quantize(Decimal('0.000001'))
        self.assertEqual(actual_balance, expected_balance)
        self.assertTrue(txn.applied)

    def test_transaction_validation_without_required_fields(self):
        """Test validation when required fields are missing"""
        # Missing source and destination
        txn = Transaction.objects.create(
            user=self.user1,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_TRANSFER_WALLET_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Transaction must have a source and a destination', str(cm.exception))

    def test_double_apply_protection(self):
        """Test that applying the same transaction twice doesn't double-apply"""
        txn = Transaction.objects.create(
            user=self.user1,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_ADD_TO_WALLET,
            state=Transaction.STATE_DONE
        )
        
        txn.apply()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1100.00'))
        
        # Apply again - should not change balance
        txn.apply()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1100.00'))

    def test_revert_unapplied_transaction(self):
        """Test that reverting an unapplied transaction does nothing"""
        txn = Transaction.objects.create(
            user=self.user1,
            destination_wallet=self.user1.wallet,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_ADD_TO_WALLET,
            state=Transaction.STATE_WAITING_TREASURY  # Not applied
        )
        
        txn.revert()
        self.user1.wallet.refresh_from_db()
        self.assertEqual(self.user1.wallet.balance, Decimal('1000.00'))  # Unchanged
        self.assertFalse(txn.applied)
