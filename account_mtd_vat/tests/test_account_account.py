from openerp.tests import common

from .utils import arbitrary

class GivenAccount(common.TransactionCase):
    def setUp(self):
        super(GivenAccount, self).setUp()
        self.account = arbitrary(self.env['account.account'].search([]))
        self.account.non_mtd_reconcilable = self.initial_non_mtd_reconcilable()

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
