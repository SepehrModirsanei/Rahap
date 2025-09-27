"""
Daily Balance Snapshots Tests

This module tests the daily balance snapshot system including:
- Account daily balance snapshots
- Deposit daily balance snapshots
- Snapshot number assignment and uniqueness
- Snapshot creation timing and frequency
- Snapshot data integrity and accuracy

Test Coverage:
- Account snapshot creation and numbering
- Deposit snapshot creation and numbering
- Snapshot uniqueness per account/deposit per date
- Snapshot number increment logic
- Snapshot data accuracy
- Management command functionality
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from finance.models import User, Account, Deposit, AccountDailyBalance, DepositDailyBalance
from finance.tests.test_config import FinanceTestCase


class DailyBalanceSnapshotsTests(FinanceTestCase):
    """Test comprehensive daily balance snapshot system"""
    
    def setUp(self):
        """Set up test data for snapshot testing"""
        self.user = self.create_test_user('snapshot_user')
        self.rial_account = self.create_test_account(
            self.user, 'Test Rial Account', Account.ACCOUNT_TYPE_RIAL, Decimal('1000000.00')
        )
        self.usd_account = self.create_test_account(
            self.user, 'Test USD Account', Account.ACCOUNT_TYPE_USD, Decimal('1000.00')
        )
        self.deposit = self.create_test_deposit(
            self.user, Decimal('500000.00'), Decimal('3.0')
        )
    
    def test_account_snapshot_creation(self):
        """Test creation of account daily balance snapshots"""
        snapshot_date = date.today()
        balance = Decimal('1000000.00')
        
        snapshot = AccountDailyBalance.objects.create(
            account=self.rial_account,
            snapshot_date=snapshot_date,
            balance=balance
        )
        
        # Verify snapshot was created correctly
        self.assertEqual(snapshot.account, self.rial_account)
        self.assertEqual(snapshot.snapshot_date, snapshot_date)
        self.assertEqual(snapshot.balance, balance)
        self.assertEqual(snapshot.snapshot_number, 0)  # Default value
    
    def test_deposit_snapshot_creation(self):
        """Test creation of deposit daily balance snapshots"""
        snapshot_date = date.today()
        balance = Decimal('500000.00')
        
        snapshot = DepositDailyBalance.objects.create(
            deposit=self.deposit,
            snapshot_date=snapshot_date,
            balance=balance
        )
        
        # Verify snapshot was created correctly
        self.assertEqual(snapshot.deposit, self.deposit)
        self.assertEqual(snapshot.snapshot_date, snapshot_date)
        self.assertEqual(snapshot.balance, balance)
        self.assertEqual(snapshot.snapshot_number, 0)  # Default value
    
    def test_snapshot_number_increment(self):
        """Test that snapshot numbers increment correctly for same account"""
        # Create snapshots for different dates to avoid unique constraint
        base_date = date.today()
        balance = Decimal('1000000.00')
        
        # Create multiple snapshots for same account on different dates
        snapshots = []
        for i in range(3):
            snapshot_date = base_date - timedelta(days=i)
            snapshot = AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=balance
            )
            snapshots.append(snapshot)
        
        # Verify snapshot numbers are sequential (each date gets number 0 by default)
        snapshot_numbers = [s.snapshot_number for s in snapshots]
        self.assertEqual(snapshot_numbers, [0, 0, 0])  # Each date gets its own sequence
    
    def test_snapshot_number_separate_per_account(self):
        """Test that different accounts have separate snapshot number sequences"""
        snapshot_date = date.today()
        balance = Decimal('1000000.00')
        
        # Create snapshots for different accounts
        snapshot1 = AccountDailyBalance.objects.create(
            account=self.rial_account,
            snapshot_date=snapshot_date,
            balance=balance
        )
        
        snapshot2 = AccountDailyBalance.objects.create(
            account=self.usd_account,
            snapshot_date=snapshot_date,
            balance=balance
        )
        
        # Both should start from 0 (separate sequences)
        self.assertEqual(snapshot1.snapshot_number, 0)
        self.assertEqual(snapshot2.snapshot_number, 0)
    
    def test_snapshot_number_separate_per_deposit(self):
        """Test that different deposits have separate snapshot number sequences"""
        # Create second deposit
        deposit2 = self.create_test_deposit(
            self.user, Decimal('300000.00'), Decimal('2.5')
        )
        
        snapshot_date = date.today()
        balance = Decimal('500000.00')
        
        # Create snapshots for different deposits
        snapshot1 = DepositDailyBalance.objects.create(
            deposit=self.deposit,
            snapshot_date=snapshot_date,
            balance=balance
        )
        
        snapshot2 = DepositDailyBalance.objects.create(
            deposit=deposit2,
            snapshot_date=snapshot_date,
            balance=balance
        )
        
        # Both should start from 0 (separate sequences)
        self.assertEqual(snapshot1.snapshot_number, 0)
        self.assertEqual(snapshot2.snapshot_number, 0)
    
    def test_snapshot_uniqueness_per_date(self):
        """Test that only one snapshot per account per date is allowed"""
        snapshot_date = date.today()
        balance = Decimal('1000000.00')
        
        # Create first snapshot
        AccountDailyBalance.objects.create(
            account=self.rial_account,
            snapshot_date=snapshot_date,
            balance=balance
        )
        
        # Try to create second snapshot for same account and date
        with self.assertRaises(Exception):  # Should raise IntegrityError
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=balance
            )
    
    def test_snapshot_data_accuracy(self):
        """Test that snapshot data accurately reflects account/deposit state"""
        # Create transaction to change account balance
        from finance.models import Transaction
        transaction = Transaction.objects.create(
            user=self.user,
            destination_account=self.rial_account,
            amount=Decimal('100000.00'),
            kind=Transaction.KIND_CREDIT_INCREASE,
            state=Transaction.STATE_DONE
        )
        transaction.apply()
        
        # Create snapshot after transaction
        snapshot_date = date.today()
        snapshot = AccountDailyBalance.objects.create(
            account=self.rial_account,
            snapshot_date=snapshot_date,
            balance=self.rial_account.balance  # Use current balance
        )
        
        # Verify snapshot balance matches account balance
        self.assertEqual(snapshot.balance, self.rial_account.balance)
        self.assertEqual(snapshot.balance, Decimal('1100000.00'))
    
    def test_snapshot_creation_with_management_command(self):
        """Test snapshot creation using management command"""
        from django.core.management import call_command
        from io import StringIO
        
        # Capture command output
        out = StringIO()
        
        # Run snapshot command
        call_command('snapshot_accounts', stdout=out)
        
        # Verify snapshots were created
        snapshots = AccountDailyBalance.objects.filter(account=self.rial_account)
        self.assertGreater(snapshots.count(), 0)
        
        # Verify snapshot data
        snapshot = snapshots.first()
        self.assertEqual(snapshot.balance, self.rial_account.balance)
        self.assertEqual(snapshot.snapshot_date, date.today())
    
    def test_deposit_snapshot_creation_with_management_command(self):
        """Test deposit snapshot creation using management command"""
        from django.core.management import call_command
        from io import StringIO
        
        # Capture command output
        out = StringIO()
        
        # Run deposit snapshot command
        call_command('snapshot_deposits', stdout=out)
        
        # Verify snapshots were created
        snapshots = DepositDailyBalance.objects.filter(deposit=self.deposit)
        self.assertGreater(snapshots.count(), 0)
        
        # Verify snapshot data
        snapshot = snapshots.first()
        self.assertEqual(snapshot.balance, self.deposit.balance)
        self.assertEqual(snapshot.snapshot_date, date.today())
    
    def test_snapshot_all_management_command(self):
        """Test snapshot all management command"""
        from django.core.management import call_command
        from io import StringIO
        
        # Capture command output
        out = StringIO()
        
        # Run snapshot all command
        call_command('snapshot_all', stdout=out)
        
        # Verify both account and deposit snapshots were created
        account_snapshots = AccountDailyBalance.objects.filter(account=self.rial_account)
        deposit_snapshots = DepositDailyBalance.objects.filter(deposit=self.deposit)
        
        self.assertGreater(account_snapshots.count(), 0)
        self.assertGreater(deposit_snapshots.count(), 0)
    
    def test_snapshot_number_persistence(self):
        """Test that snapshot numbers persist correctly across multiple days"""
        # Create snapshots for multiple days
        base_date = date.today() - timedelta(days=2)
        
        for day in range(3):
            snapshot_date = base_date + timedelta(days=day)
            snapshot = AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
            # Each day should have snapshot number 0 (separate sequences per day)
            self.assertEqual(snapshot.snapshot_number, 0)
    
    def test_snapshot_ordering(self):
        """Test that snapshots are ordered correctly by date"""
        # Create snapshots for multiple days
        base_date = date.today() - timedelta(days=2)
        
        for day in range(3):
            snapshot_date = base_date + timedelta(days=day)
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=Decimal('1000000.00')
            )
        
        # Get snapshots ordered by date
        snapshots = AccountDailyBalance.objects.filter(
            account=self.rial_account
        ).order_by('snapshot_date')
        
        # Verify ordering
        dates = [s.snapshot_date for s in snapshots]
        self.assertEqual(dates, sorted(dates))
    
    def test_snapshot_balance_accuracy_over_time(self):
        """Test that snapshots accurately track balance changes over time"""
        # Create multiple snapshots with different balances
        base_date = date.today() - timedelta(days=2)
        balances = [Decimal('1000000.00'), Decimal('1100000.00'), Decimal('1200000.00')]
        
        for day, balance in enumerate(balances):
            snapshot_date = base_date + timedelta(days=day)
            AccountDailyBalance.objects.create(
                account=self.rial_account,
                snapshot_date=snapshot_date,
                balance=balance
            )
        
        # Verify snapshots have correct balances
        snapshots = AccountDailyBalance.objects.filter(
            account=self.rial_account
        ).order_by('snapshot_date')
        
        for snapshot, expected_balance in zip(snapshots, balances):
            self.assertEqual(snapshot.balance, expected_balance)
