# -*- coding = utf-8 -*-

from odoo import models, fields, exceptions, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def list_partners_to_reconcile(self, filter_domain=False):
        line_ids = []
        if filter_domain:
            line_ids = self.search(filter_domain)
        where_clause = filter_domain and "AND l.id = ANY(%s)" or ""
        self.env.cr.execute(
            """SELECT partner_id FROM (
               SELECT l.partner_id, p.last_reconciliation_date, SUM(l.debit) AS debit, SUM(l.credit) AS credit, MAX(l.create_date) AS max_date
               FROM account_move_line l
               RIGHT JOIN account_account a ON (a.id = l.account_id)
               RIGHT JOIN res_partner p ON (l.partner_id = p.id)
                   WHERE a.reconcile IS TRUE
                   AND l.reconcile_id IS NULL
                   AND l.state <> 'draft'
                   %s
                   GROUP BY l.partner_id, p.last_reconciliation_date
               ) AS s
               WHERE debit > 0 AND credit > 0 AND (last_reconciliation_date IS NULL OR max_date > last_reconciliation_date)
               ORDER BY last_reconciliation_date"""
            % where_clause, (line_ids,))
        ids = [x[0] for x in self.env.cr.fetchall()]
        if not ids:
            return []

        # To apply the ir_rules
        partner_obj = self.env['res.partner']
        partners = partner_obj.search([('id', 'in', ids)])
        return partners.name_get()

    vat = fields.Boolean(string="VAT Posted", default=False, readonly=True)
    vat_submission_id = fields.Many2one('mtd_vat.vat_submission_logs', string='VAT Submission Period')
    unique_number = fields.Char(
        related='vat_submission_id.unique_number',
        string="HMRC Unique Number",
        readonly=True
    )
