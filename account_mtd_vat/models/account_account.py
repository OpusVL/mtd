from openerp import api, fields, models

class AccountAccount(models.Model):
    _inherit = "account.account"

    non_mtd_reconcilable = fields.Boolean()
