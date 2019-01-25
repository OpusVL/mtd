from odoo import models, fields, api


class MtdApiTokens(models.Model):
    _name = 'mtd.api'
    _description = "list of api table"

    name = fields.Char('Name', required=True, readonly=True)
    scope = fields.Char('Scope', required=True, readonly=True)
