# -*- coding: utf-8 -*-
import logging

from openerp import models, fields, api

_logger = logging.getLogger(__name__)


class MtdVATSubmissionLogs(models.Model):
    _name = 'mtd_vat.vat_submission_logs'
    _description = "Vat Submission Logs"

    name = fields.Char(string="Period")
    submission_status = fields.Char()
    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    vrn = fields.Char(string="VAT Number")
    start = fields.Date()
    end = fields.Date()
    unique_number = fields.Char()
    payment_indicator = fields.Char()
    charge_ref_number = fields.Char()
    processing_date = fields.Datetime()
    redirect_url = fields.Char()
    vat_due_sales_submit = fields.Float("1. VAT due in this period on sales and other outputs", (13, 2), readonly=True)
    vat_due_acquisitions_submit = fields.Float(
        "2. VAT due in this period on acquisitions from other EC Member States",
        (13, 2),
        readonly=True
    )
    total_vat_due_submit = fields.Float("3. Total VAT due (the sum of boxes 1 and 2)", (13, 2), readonly=True)
    vat_reclaimed_submit = fields.Float(
        "4. VAT reclaimed in this period on purchases and other inputs (including acquisitions from the EC)",
        (13, 2),
        readonly=True
    )
    net_vat_due_submit = fields.Float(
        "5. Net VAT to be paid to HMRC or reclaimed by you (Difference between boxes 3 and 4)",
        (11, 2),
        readonly=True
    )
    total_value_sales_submit = fields.Float(
        "6. Total value of sales and all other outputs excluding any VAT. (Includes box 8 figure)",
        (13, 0),
        readonly=True
    )
    total_value_purchase_submit = fields.Float(
        "7. Total value of purchases and all other inputs excluding any VAT. (Include box 9 figure)",
        (13, 0),
        readonly=True
    )
    total_value_goods_supplied_submit = fields.Float(
        "8. Total value of all supplies of goods and related costs, excluding any VAT, to other EC Member States",
        (13, 0),
        readonly=True
    )
    total_acquisitions_submit = fields.Float(
        "9. Total value of all acquisitions of goods and related costs, excluding any VAT, from other EC Member States",
        (13, 0),
        readonly=True
    )
    client_type = fields.Selection([
        ('business', 'Business'),
        ('agent', 'Agent')
    ])
    md5_integrity_value = fields.Char(string="MD5", readonly=True)


    @api.multi
    def action_Detailed_submission_Log_view(self, *args):

        detailed_submission_log_action = self.env.ref('account_mtd_vat.action_mtd_vat_detailed_submission_log').id
        detailed_submission_log_menu  = self.env.ref('account_mtd_vat.submenu_mtd_vat_detailed_submission_log').id

        redirect_url = self.redirect_url
        redirect_urlredirect_url = self.redirect_url
        redirect_url += ("/web?#page=0&limit=80&view_type=list&model=mtd_vat.vat_obligations_logs"
            + "&menu_id={menu}&action={action}".format(
            menu=detailed_submission_log_menu,
            action=detailed_submission_log_action
        ))
        context = 'unique_number: self.unique_number'

        return {'url': redirect_url,
                'type': 'ir.actions.act_url',
                'target': 'new',
                # 'domain': "['unique_number', '=', '%s']" % self.unique_number,
                'context': {'default_search_unique_number':1}
        }
