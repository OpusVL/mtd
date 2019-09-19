# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class VatCalculationTable(models.Model):
    _name = 'mtd_vat.vat_calculation_table'

    name = fields.Char(string="Originator Tax Display Name")
    taxes = fields.Char(string="Taxes Display Name")
    sum_debit = fields.Float("Sum Debit", (13, 2))
    sum_credit = fields.Float("Sum Credit", (13, 2))
    balance = fields.Float("balance", (13, 2))
    tag_id = fields.Char()
    move_line_ids = fields.Char()
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    date_vat_period = fields.Date(string='Date Vat Period')
