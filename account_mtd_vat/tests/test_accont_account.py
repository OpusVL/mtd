from odoo.tests import common
from .utils import all_records_in_model, arbitrary_from


class GivenBothReconcilableAndNonReconcilableAccounts_Tests(
        common.TransactionCase):
    def setUp(self):
        super(GivenBothReconcilableAndNonReconcilableAccounts_Tests, self).setUp()
        self.Account = self.env['account.account']
        # Make sure we have at least one of each in the database
        all_accounts = all_records_in_model(self.Account)
        reconcilable = arbitrary_from(all_accounts)
        reconcilable.non_mtd_reconcilable = True
        nonreconcilable = arbitrary_from(all_accounts - reconcilable)
        nonreconcilable.non_mtd_reconcilable = False

    def test_search_for_reconcile_True(self):
        result = self.Account.search([('reconcile', '=', True)])
        self.assertTrue(all(a.non_mtd_reconcilable for a in result),
            "All matches must be non_mtd_reconcilable")

    def test_search_for_reconcile_False(self):
        result = self.Account.search([('reconcile', '=', False)])
        self.assertTrue(all((not a.non_mtd_reconcilable) for a in result),
            "All matches must not be non_mtd_reconcilable")

class GivenAccount(common.TransactionCase):
    def setUp(self):
        super(GivenAccount, self).setUp()
        self.account = arbitrary_from(self.all_accounts)
        self.account.non_mtd_reconcilable = self.initial_non_mtd_reconcilable()

    def all_accounts(self):
        return self.env['account.account'].search([])

    def initial_non_mtd_reconcilable(self):
        self.skipTest("ABSTRACT: initial_non_mtd_reconcilable")

    def test_reconcile_True_with_context(self):
        self.assertTrue(
            self.account
            .with_context(ignore_allow_reconciliation_flag_for_mtd=True)
            .reconcile
        )


    def test_set_core_reconcile_flag_True_copies_to_non_mtd_reconcilable(self):
        self.account.reconcile = True
        self.assertTrue(self.account.non_mtd_reconcilable,
            "copied to non_mtd_reconcilable")
        self.assertTrue(self.account.reconcile,
            "reflected in computed reconcile flag")

    def test_set_core_reconcile_flag_False_copies_to_non_mtd_reconcilable(self):
        self.account.reconcile = False
        self.assertFalse(self.account.non_mtd_reconcilable,
            "copied to non_mtd_reconcilable")
        self.assertFalse(self.account.reconcile,
            "reflected in computed reconcile flag")

class GivenNonUserReconcilableAccount_Tests(GivenAccount):
    def initial_non_mtd_reconcilable(self):
        return False

    def test_reconcile_False_without_context(self):
        self.assertFalse(self.account.reconcile)


class GivenUserReconcilableAccount_Tests(GivenAccount):
    def initial_non_mtd_reconcilable(self):
        return True

    def test_reconcile_True_without_context(self):
        self.assertTrue(self.account.reconcile)