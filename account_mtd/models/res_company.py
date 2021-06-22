# -*- coding: utf-8 -*-

from openerp import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    hmrc_username = fields.Char(
        string='HMRC User ID',
    )