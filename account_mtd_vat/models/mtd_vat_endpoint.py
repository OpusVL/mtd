# -*- coding: utf-8 -*-
import logging
import urllib

from openerp import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MtdVATEndpoints(models.Model):
    _name = 'mtd_vat.vat_endpoints'
    _description = "Vat endpoints"

    name = fields.Char('Name', required=True, readonly=True)
    api_id = fields.Many2one(comodel_name="mtd.api", string="Api Name", required=True, readonly=True)
    hmrc_configuration = fields.Many2one(comodel_name="mtd.hmrc_configuration", string='HMRC Configuration')
    scope = fields.Char(related="api_id.scope")
    vrn = fields.Char('VRN')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    status = fields.Selection([
        ('o', ' O'),
        ('f', ' F'),
    ])
    gov_test_scenario = fields.Selection([
        ('SINGLE_LIABILITY', 'SINGLE_LIABILITY'),
        ('MULTIPLE_LIABILITIES', 'MULTIPLE_LIABILITIES'),
        ('DATE_RANGE_TOO_LARGE', 'DATE_RANGE_TOO_LARGE')
    ],
        string='Gov-Test-Scenario')
    x_correlation_id = fields.Char('X-CorrelationId')
    response_from_hmrc = fields.Text(string="Response From HMRC", readonly=True)
    path = fields.Char(string="sandbox_url")
    endpoint_name = fields.Char(string="which_button")
    select_vat_obligation = fields.Many2one(comodel_name='mtd_vat.vat_obligations_logs') #, compute='compute_vat_obligation')

    # def compute_vat_obligation(self):
    #     import pdb; pdb.set_trace()
    #     if self.name == "Submit VAT Returns":
    #         vat_obligations_rec = self.env['mtd_vat.vat_obligations_logs'].search([('status', '=', 'O')])
    #         for record in self:
    #             obligation_ids =[x.id for x in vat_obligations_rec]
    #             record.select_vat_obligation = [[6,0,obligation_ids]]



    @api.onchange('select_vat_obligation')
    def onchange_date_for_vat_returns(self):
        self.date_from = self.select_vat_obligation.start
        self.date_to = self.select_vat_obligation.end

    #Fields for Viewing the vat returns
    # need to display the result in the field rather than in a Text field
    view_vat_flag = fields.Boolean(default=False)
    period_key = fields.Char(related='select_vat_obligation.period_key', readonly=True)
    vat_due_sales = fields.Float("1. VAT due in this period on sales and other outputs", (13, 2), readonly=True)
    vat_due_acquisitions = fields.Float(
        "2. VAT due in this period on acquisitions from other EC Member States",
        (13, 2),
        readonly=True
    )
    total_vat_due = fields.Float("3. Total VAT due (the sum of boxes 1 and 2)", (13, 2), readonly=True)
    vat_reclaimed = fields.Float(
        "4. VAT reclaimed in this period on purchases and other inputs (including acquisitions from the EC)",
        (13, 2),
        readonly=True
    )
    net_vat_due = fields.Float(
        "5. Net VAT to be paid to HMRC or reclaimed by you (Difference between boxes 3 and 4)",
        (11, 2),
        readonly=True
    )
    total_value_sales = fields.Float(
        "6. Total value of sales and all other outputs excluding any VAT. (Includes box 8 figure)",
        (13, 0),
        readonly=True
    )
    total_value_purchase = fields.Float(
        "7. Total value of purchases and all other inputs excluding any VAT. (Include box 9 figure)",
        (13, 0),
        readonly=True
    )
    total_value_goods_supplied = fields.Float(
        "8. Total value of all supplies of goods and related costs, excluding any VAT, to other EC Member States",
        (13, 0),
        readonly=True
    )
    total_acquisitions = fields.Float(
        "9. Total value of all acquisitions of goods and related costs, excluding any VAT, from other EC Member States",
        (13, 0),
        readonly=True
    )

    # submit vat fields
    submit_vat_flag = fields.Boolean(default=False)
    period_key_submit = fields.Char(related='select_vat_obligation.period_key', readonly=True)
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
    business_declaration = fields.Char(readonly=True,
        default=("When you submit this VAT information you are making a legal declaration "
        + "\nthat the information is true and complete. "
        + "\nA false declaration can result in prosecution."))
    agent_declaration = fields.Char(readonly=True,
        default=("I confirm that my client has received a copy of the information contained "
         + "\nin this return and approved the information as being correct and "
         + "\ncomplete to the best of their knowledge and belief."))
    review_text = fields.Char(readonly=True,
        default=("Please review your VAT summary above and then tick the 'Confirm and finalise' "
                 + "checkbox and then submit to HMRC"))
    finalise = fields.Boolean(string="I confirm and finalise", default=False)

    @api.multi
    def action_vat_connection(self):
        if not self.hmrc_configuration:
            raise exceptions.Warning("Please select HMRC configuration before continuing!")
        elif not self.vrn:
            raise exceptions.Warning("Please enter the VRN")

        endpoint_record = self.env['ir.model.data'].search([
            ('res_id', '=', self.id),
            ('model', '=', 'mtd_vat.vat_endpoints')
        ])

        request_handler = {
            "mtd_vat_obligations_endpoint": "_handle_vat_obligations_endpoint",
            "mtd_vat_liabilities_endpoint": "_handle_vat_liabilities_endpoint",
            "mtd_vat_payments_endpoint": "_handle_vat_payments_endpoint",
            "mtd_vat_submit_returns_endpoint": "_handle_vat_submit_returns_endpoint",
            "mtd_vat_view_returns_endpoint": "_handle_vat_returns_view_endpoint",
        }

        handler_name = request_handler.get(endpoint_record.name)
        if handler_name:
            handle_request = getattr(self, handler_name)()
            return handle_request
        else:
            raise exceptions.Warning("Could not connect to HMRC! \nThis is not a valid HMRC service connection")

    @api.multi
    def action_retrieve_vat(self, *args):

        # RESET FOLLOWING FIELDS SO THAT USER CAN VERIFY THESE ONCE vat HAS BEEN RETRIEVED
        self.client_type = ""
        self.finalise = False
        self.response_from_hmrc = ""

        retrieve_period = self.env['account.period'].search([
            ('date_start', '=', self.date_from),
            ('date_stop', '=', self.date_to)
        ])
        context = str({'period_id': retrieve_period.id, \
                                 'fiscalyear_id': retrieve_period.fiscalyear_id.id, \
                                 'state': 'posted'})
        period_code = retrieve_period.code
        name = period_code and (':' + period_code) or ''

        retrieve_vat_code_ids = self.env['account.tax.code'].search([
            ('code', 'in', ['1','2', '3', '4', '5', '6', '7', '8', '9'])
        ])

        retrieve_sum_for_codes = retrieve_vat_code_ids.with_context(
            period_id=retrieve_period.id,
            fiscalyear_id=retrieve_period.fiscalyear_id.id,
            state='posted'
        )._sum_period(name, context)

        code_dict = {
            '1': 'vat_due_sales_submit',
            '2': 'vat_due_acquisitions_submit',
            '3': 'total_vat_due_submit',
            '4': 'vat_reclaimed_submit',
            '5': 'net_vat_due_submit',
            '6': 'total_value_sales_submit',
            '7': 'total_value_purchase_submit',
            '8': 'total_value_goods_supplied_submit',
            '9': 'total_acquisitions_submit',
        }
        if len(retrieve_period)>  0:
            self.submit_vat_flag = True
            for item in retrieve_vat_code_ids:
                if item.id in retrieve_sum_for_codes.keys() and item.code in code_dict.keys():
                    setattr(self, code_dict[item.code], retrieve_sum_for_codes[item.id])
            self.total_vat_due_submit = (self.vat_due_sales_submit + self.vat_due_acquisitions_submit)
        else:
            self.submit_vat_flag = False
            self.response_from_hmrc = (
                "No period matching to the vat obligation found Please try a different period."
            )

    def _handle_vat_obligations_endpoint(self):
        self.path = "/organisations/vat/{vrn}/obligations".format(vrn=self.vrn)
        self.endpoint_name = "vat-obligation"
        _logger.info(self.connection_button_clicked_log_message())

        return self.process_connection()

    def _handle_vat_liabilities_endpoint(self):
        self.path = "/organisations/vat/{vrn}/liabilities".format(vrn=self.vrn)
        self.endpoint_name = "vat-liabilities"

        return self.process_connection()

    def _handle_vat_payments_endpoint(self):
        self.path = "/organisations/vat/{vrn}/payments".format(vrn=self.vrn)
        self.endpoint_name = "vat-payments"

        return self.process_connection()

    def _handle_vat_returns_view_endpoint(self):
        period_key = urllib.quote_plus(self.select_vat_obligation.period_key)
        self.path = "/organisations/vat/{vrn}/returns/{key}".format(vrn=self.vrn, key=period_key)
        self.endpoint_name = "view-vat-returns"

        return self.process_connection()

    def _handle_vat_submit_returns_endpoint(self):
        period_key = urllib.quote_plus(self.select_vat_obligation.period_key)
        self.path = "/organisations/vat/{vrn}/returns".format(vrn=self.vrn)
        self.endpoint_name = "submit-vat-returns"

        return self.process_connection()

    def process_connection(self):
        # search for token
        token_record = self.env['mtd.api_tokens'].search([('api_id', '=', self.api_id.id)])
        _logger.info(
            "Vat Obligation - endpoint name {name}, and the api is :- {api_id} ".format(
                name=self.name,
                api_id=self.api_id
            )
        )
        if token_record.access_token and token_record.refresh_token:
            _logger.info(
                "Connection button Clicked - endpoint name {name}, ".format(name=self.name) +
                "We have access token and refresh token"
            )
            version = self.env['mtd_vat.issue_request'].json_command('version', self._name, self.id)
            return version
        else:
            _logger.info(
                "Vat Obligation - endpoint name {name}, ".format(name=self.name) +
                "We have no access token and refresh token found"
            )
            authorisation_tracker = self.env['mtd.api_request_tracker'].search([
                ('api_id', '=', self.api_id.id),
                ('closed', '=', False)
            ])
        create_date = fields.Datetime.from_string(authorisation_tracker.create_date)
        time_10_mins_ago = (datetime.utcnow() - timedelta(minutes=10))
        if authorisation_tracker:
            authorised_code_expired = create_date <= time_10_mins_ago
            if authorised_code_expired:
                # we can place a new request and close this request.
                authorisation_tracker.closed = 'timed_out'
                _logger.info(
                    "Connection button Clicked - endpoint name {name}, no Pending requests".format(name=self.name)
                )
                return self.env['mtd.user_authorisation'].get_user_authorisation(self._name, self)
            else:
                # The request made was within 10 mins so the user has to wait.
                raise exceptions.Warning(
                    "An authorisation request is already in process!!!\n " +
                    "Please try again later"
                )
        else:
            return self.env['mtd.user_authorisation'].get_user_authorisation(self._name, self)

    def connection_button_clicked_log_message(self):
        return "Connection button Clicked - endpoint name {name}, redirect URL:- {redirect}, Path url:- {path}".format(
                name=self.name,
                redirect=self.hmrc_configuration.redirect_url,
                path=self.path
            )


