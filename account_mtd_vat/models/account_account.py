from operator import methodcaller

from openerp import api, fields, models
from openerp.osv import osv, fields as old_api_fields


def methodproxy(method_name):
    """Return function that calls named method."""
    def _methodproxy(self, *args, **kwargs):
        method = getattr(self, method_name)
        return method(*args, **kwargs)
    return _methodproxy


class AccountAccount(models.Model):
    _inherit = "account.account"

    non_mtd_reconcilable = fields.Boolean(
        string='Allow Reconciliation',
    )


class account_account(osv.osv):
    _inherit = "account.account"

    # Must convert to compute in old API because original field was in old API
    # (in v8 at least)
    # API Documentation here:
    #   https://doc.odoo.com/v6.0/developer/2_5_Objects_Fields_Methods/field_type.html#functional-fields
    # PORTING TO NEWER ODOO: If declared in new API, do compute in new API
    _columns = {
        'reconcile': old_api_fields.function(
            fnct=methodproxy('_reconcile_flag'),
            fnct_inv=methodproxy('_set_reconcile_flag'),
            fnct_search=methodproxy('_search_for_reconcile_flag'),
            method=True,
            string='Allow Reconciliation',
            type='boolean',
            help="Check this box if this account allows reconciliation of journal items."),
    }

    def _reconciliation_allowed_on_all_accounts(self, context):
        return (
            (context or {})
            .get('reconciliation_allowed_on_all_accounts', False)
        )

    def _reconcile_flag(self, cr, uid, ids, field_name, arg, context):
        assert field_name == 'reconcile', "Only handles reconcile flag"
        if self._reconciliation_allowed_on_all_accounts(context):
            return {id_: {'reconcile': True} for id_ in ids}
        else:
            accounts = self.read(
                cr, uid, ids, ['id', 'non_mtd_reconcilable'], context=context)
            return {
                account['id']: account['non_mtd_reconcilable']
                for account in accounts
            }

    def _set_reconcile_flag(self, cr, uid, ids, field_name, field_value, arg,
            context):
        assert field_name == 'reconcile', "Only handles reconcile flag"
        updates = {'non_mtd_reconcilable': field_value}
        return self.write(cr, uid, ids, updates, context=context)

    def _search_for_reconcile_flag(self, cr, uid, obj, name, args, context):
        # From the old API docs:
        # obj is the same as self, and name receives the field name.
        # args is a list of 3-part tuples containing search criteria for this field,
        # although the search function may be called separately for each tuple.
        assert name == 'reconcile', "Only handles reconcile flag"
        if self._reconciliation_allowed_on_all_accounts(context):
            match_any_account = []
            return match_any_account
        else:
            return [
                ('non_mtd_reconcilable', operator, value)
                for (field, operator, value) in args
                if field == 'reconcile'
            ]
