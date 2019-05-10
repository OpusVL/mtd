# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = "res.company"

    hmrc_posting_created = fields.Boolean(default=False)