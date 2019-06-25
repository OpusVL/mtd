from operator import methodcaller

from openerp import api, fields, models
from openerp.osv import osv, fields as old_api_fields

class AccountAccount(models.Model):
    _inherit = "account.account"

    non_mtd_reconcilable = fields.Boolean()


class account_account(osv.osv):
    _inherit = "account.account"

    # Must convert to compute in old API because original field was in old API
    # (in v8 at least)
    # PORTING TO NEWER ODOO: If declared in new API, do compute in new API
    _columns = {
        'reconcile': old_api_fields.function(
            fnct=lambda self, *args, **kwargs:
                self._reconcile_flag(*args, **kwargs),
            method=True,
            string='Allow Reconciliation',
            type='boolean',
            help="Check this box if this account allows reconciliation of journal items."),
    }

    def _reconcile_flag(self, cr, uid, ids, field_name, arg, context):
        allow_reconciliation_on_all_accounts = (
            (context or {})
            .get('ignore_allow_reconciliation_flag_for_mtd', False)
        )
        if allow_reconciliation_on_all_accounts:
            return {id_: {'reconcile': True} for id_ in ids}
        else:
            accounts = self.read(
                cr, uid, ids, ['id', 'non_mtd_reconcilable'], context=context)
            return {
                account['id']: account['non_mtd_reconcilable']
                for account in accounts
            }
