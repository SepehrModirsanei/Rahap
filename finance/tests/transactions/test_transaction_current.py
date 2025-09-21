from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

from finance.models import Account, Deposit, Transaction


class TransactionCurrentTests(TestCase):
    """Tests for current transaction functionality including rial account validation and balance changes"""
    
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass'
        )
        
        # Create different types of accounts
        cls.rial_account = Account.objects.create(
            user=cls.user,
            name='Rial Account',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('1000.00'),
            monthly_profit_rate=Decimal('2.5')
        )
        
        cls.foreign_account = Account.objects.create(
            user=cls.user,
            name='Foreign Account',
            account_type=Account.ACCOUNT_TYPE_FOREIGN,
            initial_balance=Decimal('100.00'),
            monthly_profit_rate=Decimal('1.0')
        )
        
        cls.gold_account = Account.objects.create(
            user=cls.user,
            name='Gold Account',
            account_type=Account.ACCOUNT_TYPE_GOLD,
            initial_balance=Decimal('10.50'),
            monthly_profit_rate=Decimal('0.5')
        )

    # ==================== RIAL ACCOUNT VALIDATION TESTS ====================
    
    def test_credit_increase_rial_account_success(self):
        """Test that credit increase works with rial accounts"""
        txn = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        # Should not raise ValidationError
        txn.clean()
        txn.apply()
        self.assertTrue(txn.applied)

    def test_credit_increase_foreign_account_fails(self):
        """Test that credit increase fails with foreign accounts"""
        txn = Transaction.objects.create(
            user=self.user,
            destination_account=self.foreign_account,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Credit increase can only be applied to rial accounts', str(cm.exception))

    def test_credit_increase_gold_account_fails(self):
        """Test that credit increase fails with gold accounts"""
        txn = Transaction.objects.create(
            user=self.user,
            destination_account=self.gold_account,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Credit increase can only be applied to rial accounts', str(cm.exception))

    def test_withdrawal_request_rial_account_success(self):
        """Test that withdrawal request works with rial accounts"""
        txn = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE,
            withdrawal_card_number='1234567890123456'
        )
        
        # Should not raise ValidationError
        txn.clean()
        txn.apply()
        self.assertTrue(txn.applied)

    def test_withdrawal_request_foreign_account_fails(self):
        """Test that withdrawal request fails with foreign accounts"""
        txn = Transaction.objects.create(
            user=self.user,
            source_account=self.foreign_account,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Withdrawal request can only be applied to rial accounts', str(cm.exception))

    def test_withdrawal_request_gold_account_fails(self):
        """Test that withdrawal request fails with gold accounts"""
        txn = Transaction.objects.create(
            user=self.user,
            source_account=self.gold_account,
            amount=Decimal('100.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE
        )
        
        with self.assertRaises(ValidationError) as cm:
            txn.clean()
        self.assertIn('Withdrawal request can only be applied to rial accounts', str(cm.exception))

    # ==================== BALANCE CHANGE TESTS ====================
    
    def test_credit_increase_affects_balance(self):
        """Test that credit increase transaction increases account balance"""
        initial_balance = self.rial_account.balance
        self.assertEqual(initial_balance, Decimal('1000.00'))
        
        # Create and apply credit increase transaction
        txn = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('500.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        # Check that balance increased
        self.rial_account.refresh_from_db()
        new_balance = self.rial_account.balance
        self.assertEqual(new_balance, Decimal('1500.00'))  # 1000 + 500
        self.assertTrue(txn.applied)

    def test_withdrawal_request_affects_balance(self):
        """Test that withdrawal request transaction decreases account balance"""
        initial_balance = self.rial_account.balance
        self.assertEqual(initial_balance, Decimal('1000.00'))
        
        # Create and apply withdrawal request transaction
        txn = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('300.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE,
            withdrawal_card_number='1234567890123456'
        )
        txn.apply()
        
        # Check that balance decreased
        self.rial_account.refresh_from_db()
        new_balance = self.rial_account.balance
        self.assertEqual(new_balance, Decimal('700.00'))  # 1000 - 300
        self.assertTrue(txn.applied)

    def test_multiple_credit_increases_accumulate(self):
        """Test that multiple credit increase transactions accumulate correctly"""
        initial_balance = self.rial_account.balance
        self.assertEqual(initial_balance, Decimal('1000.00'))
        
        # Create multiple credit increase transactions
        txn1 = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('200.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        txn1.apply()
        
        txn2 = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('300.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        txn2.apply()
        
        # Check that balance increased by both amounts
        self.rial_account.refresh_from_db()
        new_balance = self.rial_account.balance
        self.assertEqual(new_balance, Decimal('1500.00'))  # 1000 + 200 + 300
        self.assertTrue(txn1.applied)
        self.assertTrue(txn2.applied)

    def test_multiple_withdrawal_requests_accumulate(self):
        """Test that multiple withdrawal request transactions accumulate correctly"""
        initial_balance = self.rial_account.balance
        self.assertEqual(initial_balance, Decimal('1000.00'))
        
        # Create multiple withdrawal request transactions
        txn1 = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('150.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE,
            withdrawal_card_number='1234567890123456'
        )
        txn1.apply()
        
        txn2 = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('250.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE,
            withdrawal_sheba_number='IR1234567890123456789012'
        )
        txn2.apply()
        
        # Check that balance decreased by both amounts
        self.rial_account.refresh_from_db()
        new_balance = self.rial_account.balance
        self.assertEqual(new_balance, Decimal('600.00'))  # 1000 - 150 - 250
        self.assertTrue(txn1.applied)
        self.assertTrue(txn2.applied)

    def test_mixed_credit_increase_and_withdrawal(self):
        """Test that credit increase and withdrawal request transactions work together"""
        initial_balance = self.rial_account.balance
        self.assertEqual(initial_balance, Decimal('1000.00'))
        
        # Create credit increase transaction
        credit_txn = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('800.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        credit_txn.apply()
        
        # Check balance after credit increase
        self.rial_account.refresh_from_db()
        balance_after_credit = self.rial_account.balance
        self.assertEqual(balance_after_credit, Decimal('1800.00'))  # 1000 + 800
        
        # Create withdrawal request transaction
        withdrawal_txn = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            amount=Decimal('400.00'),
            kind=Transaction.KIND_WITHDRAWAL_REQUEST,
            state=Transaction.STATE_DONE,
            withdrawal_card_number='1234567890123456'
        )
        withdrawal_txn.apply()
        
        # Check final balance
        self.rial_account.refresh_from_db()
        final_balance = self.rial_account.balance
        self.assertEqual(final_balance, Decimal('1400.00'))  # 1000 + 800 - 400
        self.assertTrue(credit_txn.applied)
        self.assertTrue(withdrawal_txn.applied)

    # ==================== ACCOUNT TO ACCOUNT TRANSFER TESTS ====================
    
    def test_account_to_account_transfer_same_currency(self):
        """Test transferring between accounts of the same currency type"""
        # Create another rial account for same-currency transfer
        rial_account2 = Account.objects.create(
            user=self.user,
            name='Rial Account 2',
            account_type=Account.ACCOUNT_TYPE_RIAL,
            initial_balance=Decimal('200.00'),
            monthly_profit_rate=Decimal('2.0')
        )
        
        txn = Transaction.objects.create(
            user=self.user,
            source_account=self.rial_account,
            destination_account=rial_account2,
            amount=Decimal('300.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            state=Transaction.STATE_DONE
        )
        txn.apply()
        
        self.rial_account.refresh_from_db()
        rial_account2.refresh_from_db()
        self.assertEqual(self.rial_account.balance, Decimal('700.00'))  # 1000 - 300
        self.assertEqual(rial_account2.balance, Decimal('500.00'))  # 200 + 300
        self.assertTrue(txn.applied)
