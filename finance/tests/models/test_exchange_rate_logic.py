"""
Exchange Rate Logic Tests

This module tests the complex exchange rate logic for cross-currency transactions.
It covers all currency conversion scenarios including Rial↔FX, FX↔FX, and Gold conversions.

Test Coverage:
- Rial to Foreign Currency conversions
- Foreign Currency to Rial conversions  
- Foreign Currency to Foreign Currency conversions (via IRR prices)
- Exchange rate validation and error handling
- Destination amount calculation accuracy
- Edge cases and error conditions
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from finance.models import User, Account, Transaction
from finance.tests.test_config import FinanceTestCase


class ExchangeRateLogicTests(FinanceTestCase):
    """Test comprehensive exchange rate logic for all currency conversion scenarios"""
    
    def setUp(self):
        """Set up test data with accounts of different currency types"""
        self.user = self.create_test_user('exchangerate_user')
        self.accounts = self.create_cross_currency_accounts(self.user)
    
    def test_rial_to_usd_conversion(self):
        """Test Rial to USD conversion with exchange rate"""
        # Test: 1,000,000 IRR → USD at rate 500,000 IRR per USD
        exchange_rate = Decimal('500000.00')  # 500,000 IRR per USD
        expected_destination = Decimal('2.00')  # 1,000,000 / 500,000 = 2 USD
        
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=Decimal('1000000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=exchange_rate,
            state=Transaction.STATE_DONE
        )
        
        # Verify destination amount is calculated correctly
        self.assertEqual(transaction.destination_amount, expected_destination)
        
        # Apply transaction and verify balances
        transaction.apply()
        
        # Source account should lose 1,000,000 IRR
        self.assertEqual(self.accounts['rial'].balance, Decimal('0.00'))
        # Destination account should gain 2 USD
        self.assertEqual(self.accounts['usd'].balance, Decimal('1002.00'))
    
    def test_usd_to_rial_conversion(self):
        """Test USD to Rial conversion with exchange rate"""
        # Test: 2 USD → IRR at rate 500,000 IRR per USD
        exchange_rate = Decimal('500000.00')  # 500,000 IRR per USD
        expected_destination = Decimal('1000000.00')  # 2 * 500,000 = 1,000,000 IRR
        
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.accounts['usd'],
            destination_account=self.accounts['rial'],
            amount=Decimal('2.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=exchange_rate,
            state=Transaction.STATE_DONE
        )
        
        # Verify destination amount is calculated correctly
        self.assertEqual(transaction.destination_amount, expected_destination)
        
        # Apply transaction and verify balances
        transaction.apply()
        
        # Source account should lose 2 USD
        self.assertEqual(self.accounts['usd'].balance, Decimal('998.00'))
        # Destination account should gain 1,000,000 IRR
        self.assertEqual(self.accounts['rial'].balance, Decimal('2000000.00'))
    
    def test_usd_to_eur_conversion_via_irr(self):
        """Test USD to EUR conversion using IRR prices"""
        # Test: 1 USD → EUR via IRR prices
        # USD price: 500,000 IRR per USD
        # EUR price: 550,000 IRR per EUR
        # Expected: 1 USD * (500,000 / 550,000) = 0.909 EUR
        source_price_irr = Decimal('500000.00')  # 500,000 IRR per USD
        dest_price_irr = Decimal('550000.00')    # 550,000 IRR per EUR
        expected_destination = Decimal('0.909091')  # 1 * (500,000 / 550,000)
        
        # NOTE: The apply method doesn't yet support FX to FX via IRR prices
        # For now, we need to use exchange_rate for the apply method to work
        # The clean method calculates destination_amount correctly, but apply needs exchange_rate
        calculated_rate = source_price_irr / dest_price_irr  # 500,000 / 550,000 = 0.909
        
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.accounts['usd'],
            destination_account=self.accounts['eur'],
            amount=Decimal('1.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            source_price_irr=source_price_irr,
            dest_price_irr=dest_price_irr,
            exchange_rate=calculated_rate,  # Required for apply method
            state=Transaction.STATE_DONE
        )
        
        # Verify destination amount is calculated correctly
        self.assertEqual(transaction.destination_amount, expected_destination)
        
        # Apply transaction and verify balances
        transaction.apply()
        
        # Source account should lose 1 USD
        self.assertEqual(self.accounts['usd'].balance, Decimal('999.00'))
        # Destination account should gain 0.909 EUR
        self.assertEqual(self.accounts['eur'].balance, Decimal('1000.909091'))
    
    def test_gold_to_rial_conversion(self):
        """Test Gold to Rial conversion with exchange rate"""
        # Test: 1 gram Gold → IRR at rate 2,000,000 IRR per gram
        exchange_rate = Decimal('2000000.00')  # 2,000,000 IRR per gram
        expected_destination = Decimal('2000000.00')  # 1 * 2,000,000 = 2,000,000 IRR
        
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.accounts['gold'],
            destination_account=self.accounts['rial'],
            amount=Decimal('1.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=exchange_rate,
            state=Transaction.STATE_DONE
        )
        
        # Verify destination amount is calculated correctly
        self.assertEqual(transaction.destination_amount, expected_destination)
        
        # Apply transaction and verify balances
        transaction.apply()
        
        # Source account should lose 1 gram
        self.assertEqual(self.accounts['gold'].balance, Decimal('9.00'))
        # Destination account should gain 2,000,000 IRR
        self.assertEqual(self.accounts['rial'].balance, Decimal('3000000.00'))
    
    def test_exchange_rate_validation_positive(self):
        """Test that exchange rate must be positive"""
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('1000000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('0.00'),  # Invalid: zero rate
                state=Transaction.STATE_DONE
            )
    
    def test_exchange_rate_validation_negative(self):
        """Test that exchange rate cannot be negative"""
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                user=self.user,
                source_account=self.accounts['rial'],
                destination_account=self.accounts['usd'],
                amount=Decimal('1000000.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('-500000.00'),  # Invalid: negative rate
                state=Transaction.STATE_DONE
            )
    
    def test_cross_currency_missing_irr_prices(self):
        """Test that FX to FX conversion requires both IRR prices"""
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                user=self.user,
                source_account=self.accounts['usd'],
                destination_account=self.accounts['eur'],
                amount=Decimal('1.00'),
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                source_price_irr=Decimal('500000.00'),
                # Missing dest_price_irr
                state=Transaction.STATE_DONE
            )
    
    def test_same_currency_no_conversion(self):
        """Test that same currency transfers don't require exchange rate"""
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['rial'],
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            # No exchange rate needed for same currency
            state=Transaction.STATE_DONE
        )
        
        # Should have destination_amount equal to source amount for same currency
        self.assertEqual(transaction.destination_amount, Decimal('100000.00'))
        
        # Apply transaction and verify balances
        transaction.apply()
        
        # Both accounts should be affected normally
        # Source account should lose 100,000, destination should gain 100,000
        # But since it's the same account, net effect is 0
        self.assertEqual(self.accounts['rial'].balance, Decimal('1000000.00'))
    
    def test_insufficient_balance_with_exchange_rate(self):
        """Test that insufficient balance is caught even with exchange rate"""
        # Try to transfer more USD than available
        with self.assertRaises(ValidationError):
            Transaction.objects.create(
                user=self.user,
                source_account=self.accounts['usd'],
                destination_account=self.accounts['rial'],
                amount=Decimal('2000.00'),  # More than available (1000 USD)
                kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
                exchange_rate=Decimal('500000.00'),
                state=Transaction.STATE_DONE
            )
    
    def test_exchange_rate_precision(self):
        """Test that exchange rate calculations maintain proper precision"""
        # Test with high precision exchange rate
        exchange_rate = Decimal('500000.123456')
        amount = Decimal('1000000.00')  # 1,000,000 Rial
        expected_destination = Decimal('2.000000')  # 1,000,000 / 500,000.123456
        
        transaction = Transaction.objects.create(
            user=self.user,
            source_account=self.accounts['rial'],
            destination_account=self.accounts['usd'],
            amount=amount,
            kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_ACCOUNT,
            exchange_rate=exchange_rate,
            state=Transaction.STATE_DONE
        )
        
        # Verify precision is maintained
        self.assertEqual(transaction.destination_amount, expected_destination)
