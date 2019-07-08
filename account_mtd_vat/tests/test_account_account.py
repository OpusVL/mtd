from openerp.tests import common

from .utils import all_records_in_model, arbitrary_from


class GivenBothReconcilableAndNonReconcilableAccounts_Tests(
        common.TransactionCase):
    def setUp(self):
        super(GivenBothReconcilableAndNonReconcilableAccounts_Tests, self).setUp()
        self.Account = self.env['account.account']
        self._make_us_have_at_least_one_reconcilable_and_unreconcilable_account()

    def _make_us_have_at_least_one_reconcilable_and_unreconcilable_account(self):
        all_accounts = all_records_in_model(self.Account)
        reconcilable = arbitrary_from(all_accounts)
        reconcilable.is_reconcilable_by_user = True
        nonreconcilable = arbitrary_from(all_accounts - reconcilable)
        nonreconcilable.is_reconcilable_by_user = False

    def test_search_for_reconcile_True(self):
        result = self.Account.search([('reconcile', '=', True)])
        self.assertTrue(all(a.is_reconcilable_by_user for a in result),
            "All matches must be is_reconcilable_by_user")

    def test_search_for_reconcile_False(self):
        result = self.Account.search([('reconcile', '=', False)])
        self.assertTrue(all((not a.is_reconcilable_by_user) for a in result),
            "All matches must not be is_reconcilable_by_user")


class GivenAccount(common.TransactionCase):
    def setUp(self):
        super(GivenAccount, self).setUp()
        self.account = arbitrary_from(
            all_records_in_model(self.env['account.account']))
        self.account.is_reconcilable_by_user = self.initial_is_reconcilable_by_user()

    def initial_is_reconcilable_by_user(self):
        self.skipTest("ABSTRACT: initial_is_reconcilable_by_user")

    def test_reconcile_True_with_context(self):
        self.assertTrue(
            self.account
            .with_context(reconciliation_allowed_on_all_accounts=True)
            .reconcile
        )

    def test_set_core_reconcile_flag_True_copies_to_is_reconcilable_by_user(self):
        self.account.reconcile = True
        self.assertTrue(self.account.is_reconcilable_by_user,
            "copied to is_reconcilable_by_user")
        self.assertTrue(self.account.reconcile,
            "reflected in computed reconcile flag")

    def test_set_core_reconcile_flag_False_copies_to_is_reconcilable_by_user(self):
        self.account.reconcile = False
        self.assertFalse(self.account.is_reconcilable_by_user,
            "copied to is_reconcilable_by_user")
        self.assertFalse(self.account.reconcile,
            "reflected in computed reconcile flag")


class GivenNonUserReconcilableAccount_Tests(GivenAccount):
    def initial_is_reconcilable_by_user(self):
        return False

    def test_reconcile_False_without_context(self):
        self.assertFalse(self.account.reconcile)


class GivenUserReconcilableAccount_Tests(GivenAccount):
    def initial_is_reconcilable_by_user(self):
        return True

    def test_reconcile_True_without_context(self):
        self.assertTrue(self.account.reconcile)
