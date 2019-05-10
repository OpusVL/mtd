# -*- coding = utf-8 -*-

import logging

from odoo import models, fields, api, exceptions


class HMRCPostingConfiguration(models.Model):

    _name = 'mtd_vat.hmrc_posting_configuration'
    _description = "HMRC Posting Configuration"

    name = fields.Many2one(comodel_name="res.company", string="Company", required=True)
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal", required=True)
    output_account = fields.Many2one(comodel_name="account.account", string="Tax Output Account", required=True)
    input_account = fields.Many2one(comodel_name="account.account", string="Tax Input Account", required=True)
    liability_account = fields.Many2one(comodel_name="account.account", string="HMRC Liability Account", required=True)
    cutoff_date = fields.Date(string='MTD Cutoff Date', required=True, help="Include transaction from this period")

    company_journal = fields.Integer(compute="_compute_company_id")

    @api.onchange('name')
    def onchange_reset_fields(self):
        self.journal_id = False
        self.output_account = False
        self.input_account = False
        self.liability_account = False

    @api.depends('name')
    def _compute_company_id(self):
        self.company_journal = self.name.id

    @api.model
    def create(self, vals):

        res = super(HMRCPostingConfiguration, self).create(vals)
        company_id = res.name.id

        res_partner = self.env['res.company'].search([('id', '=', company_id)])

        if len(res_partner) == 1:
            res_partner.hmrc_posting_created = True

        return res
