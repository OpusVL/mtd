from odoo.tests import common
from .utils import all_records_in_model, arbitrary_from


class GivenBothReconcilableAndNonReconcilableAccounts_Tests(
        common.TransactionCase):
    def setUp(self):
        super(GivenBothReconcilableAndNonReconcilableAccounts_Tests, self).setUp()
        self.Account = self.env['account.account']


class GivenAccount(common.TransactionCase):


    def setUp(self):
        super(GivenAccount, self).setUp()
        self.account = arbitrary_from(
            all_records_in_model(self.env['account.account']))

    def test_reconcile_True_with_context(self):
        self.assertTrue(
            self.account
            .with_context(reconciliation_allowed_on_all_accounts=True)
            .reconcile
        )

class GivenNonUserReconcilableAccount_Tests(GivenAccount):

    def test_reconcile_False_without_context(self):
        self.assertFalse(self.account.reconcile)


class GivenUserReconcilableAccount_Tests(GivenAccount):

    def test_reconcile_True_without_context(self):
        self.assertTrue(self.account.reconcile)
