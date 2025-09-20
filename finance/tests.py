from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import Wallet, Account, Deposit, Transaction


class AdminCRUDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='adminpass'
        )
        cls.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='userpass1'
        )
        cls.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='userpass2'
        )
        # Ensure wallets are created
        if not hasattr(cls.admin, 'wallet'):
            Wallet.objects.create(user=cls.admin)
        if not hasattr(cls.user1, 'wallet'):
            Wallet.objects.create(user=cls.user1)
        if not hasattr(cls.user2, 'wallet'):
            Wallet.objects.create(user=cls.user2)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_admin_site_loads(self):
        resp = self.client.get('/admin/')
        self.assertEqual(resp.status_code, 200)

    # User admin
    def test_user_admin_add_change_delete(self):
        # add
        url_add = reverse('admin:finance_user_add')
        resp = self.client.get(url_add)
        self.assertEqual(resp.status_code, 200)
        post_data = {
            'username': 'newuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'is_staff': 'on',
        }
        resp = self.client.post(url_add, post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        User = get_user_model()
        new_user = User.objects.get(username='newuser')
        # change
        url_change = reverse('admin:finance_user_change', args=[new_user.pk])
        resp = self.client.get(url_change)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            url_change,
            {
                'username': 'newuser',
                'email': 'new@ex.com',
                'is_active': 'on',
                'is_staff': 'on',
                'is_superuser': '',
                'last_login_0': '',
                'last_login_1': '',
                'date_joined_0': '2000-01-01',
                'date_joined_1': '00:00:00',
                'groups': [],
                'user_permissions': [],
                'password': new_user.password,
                'first_name': '',
                'last_name': '',
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        # delete
        url_delete = reverse('admin:finance_user_delete', args=[new_user.pk])
        resp = self.client.get(url_delete)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(url_delete, {'post': 'yes'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    # Wallet admin
    def test_wallet_admin_list_add_change_delete(self):
        # list
        url_list = reverse('admin:finance_wallet_changelist')
        self.assertEqual(self.client.get(url_list).status_code, 200)
        # add: create third user to assign wallet manually
        User = get_user_model()
        user3 = User.objects.create_user('user3', password='xpass')
        # Ensure wallet exists first
        if not hasattr(user3, 'wallet'):
            Wallet.objects.create(user=user3)
        # Delete to test manual add
        user3.wallet.delete()
        url_add = reverse('admin:finance_wallet_add')
        resp = self.client.post(
            url_add,
            {'user': user3.pk, 'balance': '123.45', 'currency': 'IRR'},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        wallet = Wallet.objects.get(user=user3)
        # change
        url_change = reverse('admin:finance_wallet_change', args=[wallet.pk])
        resp = self.client.post(
            url_change,
            {'user': user3.pk, 'balance': '200.00', 'currency': 'IRR'},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        wallet.refresh_from_db()
        self.assertEqual(str(Decimal(wallet.balance).quantize(Decimal('0.01'))), '200.00')
        # delete
        url_delete = reverse('admin:finance_wallet_delete', args=[wallet.pk])
        resp = self.client.post(url_delete, {'post': 'yes'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    # Account admin
    def test_account_admin_crud(self):
        url_list = reverse('admin:finance_account_changelist')
        self.assertEqual(self.client.get(url_list).status_code, 200)
        url_add = reverse('admin:finance_account_add')
        resp = self.client.post(
            url_add,
            {
                'user': self.user1.pk,
                'wallet': self.user1.wallet.pk,
                'name': 'My Rial',
                'account_type': 'rial',
                'balance': '0.00',
                'monthly_profit_rate': '2.5',
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        acc = Account.objects.get(user=self.user1, name='My Rial')
        url_change = reverse('admin:finance_account_change', args=[acc.pk])
        resp = self.client.post(
            url_change,
            {
                'user': self.user1.pk,
                'wallet': self.user1.wallet.pk,
                'name': 'My Rial 2',
                'account_type': 'rial',
                'balance': '10.00',
                'monthly_profit_rate': '3.0',
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        acc.refresh_from_db()
        self.assertEqual(acc.name, 'My Rial 2')
        url_delete = reverse('admin:finance_account_delete', args=[acc.pk])
        resp = self.client.post(url_delete, {'post': 'yes'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    # Deposit admin
    def test_deposit_admin_crud(self):
        # fund user1 wallet first
        w = self.user1.wallet
        w.balance = Decimal('100.00')
        w.save(update_fields=['balance'])
        url_add = reverse('admin:finance_deposit_add')
        resp = self.client.post(
            url_add,
            {
                'user': self.user1.pk,
                'wallet': self.user1.wallet.pk,
                'amount': '30.00',
                'monthly_profit_rate': '1.5',
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        dep = Deposit.objects.get(user=self.user1)
        # Signal auto-funds deposit and debits wallet
        w.refresh_from_db(); dep.refresh_from_db()
        self.assertEqual(str(Decimal(w.balance).quantize(Decimal('0.01'))), '70.00')
        # delete
        url_delete = reverse('admin:finance_deposit_delete', args=[dep.pk])
        resp = self.client.post(url_delete, {'post': 'yes'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    # Transaction admin
    def test_transaction_admin_crud(self):
        # create wallets ensured by signal
        w1 = self.user1.wallet
        w2 = self.user2.wallet
        url_add = reverse('admin:finance_transaction_add')
        resp = self.client.post(
            url_add,
            {
                'user': self.user1.pk,
                'source_wallet': w2.pk,  # arbitrary for admin
                'destination_wallet': w1.pk,
                'source_account': '',
                'destination_account': '',
                'amount': '50.00',
                'kind': 'wallet_to_wallet',
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        txn = Transaction.objects.latest('id')
        url_change = reverse('admin:finance_transaction_change', args=[txn.pk])
        resp = self.client.post(
            url_change,
            {
                'user': self.user1.pk,
                'source_wallet': w2.pk,
                'destination_wallet': w1.pk,
                'source_account': '',
                'destination_account': '',
                'amount': '75.00',
                'kind': 'wallet_to_wallet',
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        url_delete = reverse('admin:finance_transaction_delete', args=[txn.pk])
        resp = self.client.post(url_delete, {'post': 'yes'}, follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_transaction_types_and_exchange(self):
        u = self.user1
        w = u.wallet
        # Add to wallet
        txn = Transaction.objects.create(user=u, destination_wallet=w, amount=100, kind=Transaction.KIND_ADD_TO_WALLET, state=Transaction.STATE_DONE)
        txn.apply()
        w.refresh_from_db()
        self.assertEqual(str(Decimal(w.balance).quantize(Decimal('0.01'))), '100.00')
        # Remove from wallet
        txn = Transaction.objects.create(user=u, source_wallet=w, amount=20, kind=Transaction.KIND_REMOVE_FROM_WALLET, state=Transaction.STATE_DONE)
        txn.apply()
        w.refresh_from_db()
        self.assertEqual(str(Decimal(w.balance).quantize(Decimal('0.01'))), '80.00')
        # Create non-rial account
        acc_fx = Account.objects.create(user=u, wallet=w, name='USD', account_type='foreign', balance=0, monthly_profit_rate=0)
        # Wallet(IRR) -> non-rial account with exchange (rate=IRR per unit FX)
        txn = Transaction.objects.create(user=u, source_wallet=w, destination_account=acc_fx, amount=50, kind=Transaction.KIND_TRANSFER_WALLET_TO_ACCOUNT, exchange_rate=500000, state=Transaction.STATE_DONE)
        txn.apply()
        w.refresh_from_db(); acc_fx.refresh_from_db()
        # 50 IRR to account at rate 500k IRR per USD => 50/500000 = 0.0001
        self.assertEqual(str(acc_fx.balance), '0.000100')
        # Account(FX) -> Wallet(IRR) with exchange
        txn = Transaction.objects.create(user=u, source_account=acc_fx, destination_wallet=w, amount=Decimal('0.0001'), kind=Transaction.KIND_TRANSFER_ACCOUNT_TO_WALLET, exchange_rate=500000, state=Transaction.STATE_DONE)
        txn.apply()
        w.refresh_from_db(); acc_fx.refresh_from_db()
        # Wallet credited by amount * rate = 0.0001 * 500000 = 50
        self.assertEqual(str(Decimal(w.balance).quantize(Decimal('0.01'))), '80.00')
        # Create deposit and initialize from wallet
        dep = Deposit.objects.create(user=u, wallet=w, amount=30, monthly_profit_rate=1)
        w.refresh_from_db(); dep.refresh_from_db()
        self.assertEqual(str(Decimal(w.balance).quantize(Decimal('0.01'))), '50.00')


# Create your tests here.
