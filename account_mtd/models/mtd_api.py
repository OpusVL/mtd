from openerp import models, fields, api


class MtdApiTokens(models.Model):
    _name = 'mtd.api'
    _description = "list of api table"

    name = fields.Char(required=True, readonly=True)
    scope = fields.Char(required=True, readonly=True)
