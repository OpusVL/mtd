# -*- coding: utf-8 -*-
import logging
import urllib

from openerp import models, fields, api, exceptions
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class GovTestScenario(models.Model):
    _name = 'gov.test.scenario'

    name = fields.Char()
    mtd_vat_obligations_endpoint = fields.Boolean()
    mtd_vat_liabilities_endpoint = fields.Boolean()
    mtd_vat_payments_endpoint = fields.Boolean()
    mtd_vat_submit_returns_endpoint = fields.Boolean()
    mtd_vat_view_returns_endpoint = fields.Boolean()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        endpoint_name = self.env.context.get('endpoint_name')
        endpoint_id = self.env['mtd_vat.vat_endpoints'].search([('name', '=', endpoint_name)]).id
        endpoint_record = self.env['ir.model.data'].search([
            ('res_id', '=', endpoint_id),
            ('model', '=', 'mtd_vat.vat_endpoints')
        ])
        args.append((endpoint_record.name, '=', True))
        return super(GovTestScenario, self).name_search(name=name, args=args, operator=operator, limit=limit)


class MtdVATEndpoints(models.Model):
    _name = 'mtd_vat.vat_endpoints'
    _description = "Vat endpoints"

    name = fields.Char('Name', required=True, readonly=True)
    api_id = fields.Many2one(comodel_name="mtd.api", string="Api Name", required=True, readonly=True)
    hmrc_configuration = fields.Many2one(comodel_name="mtd.hmrc_configuration", string='HMRC Configuration')
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    scope = fields.Char(related="api_id.scope")
    vrn = fields.Char(related="company_id.vrn", string="VAT Number", readonly=True)

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.vrn = self.company_id.vrn

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    status = fields.Selection([
        ('o', ' O'),
        ('f', ' F'),
    ])
    gov_test_scenario = fields.Many2one('gov.test.scenario', string='Gov-Test-Scenario')
    x_correlation_id = fields.Char('X-CorrelationId')
    response_from_hmrc = fields.Text(string="Response From HMRC", readonly=True)
    path = fields.Char(string="sandbox_url")
    endpoint_name = fields.Char(string="which_button")
    select_vat_obligation = fields.Many2one(comodel_name='mtd_vat.vat_obligations_logs')

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
    vat_due_sales_submit = fields.Float("1. VAT due in this period on sales and other outputs", (13, 2), default=0.00)
    vat_due_acquisitions_submit = fields.Float(
        "2. VAT due in this period on acquisitions from other EC Member States",
        (13, 2),
        default=0.00
    )
    total_vat_due_submit = fields.Float("3. Total VAT due (the sum of boxes 1 and 2)", (13, 2), default=0.00)
    vat_reclaimed_submit = fields.Float(
        "4. VAT reclaimed in this period on purchases and other inputs (including acquisitions from the EC)",
        (13, 2),
        default=0.00
    )
    net_vat_due_submit = fields.Float(
        "5. Net VAT to be paid to HMRC or reclaimed by you (Difference between boxes 3 and 4)",
        (11, 2),
        default=0.00
    )
    total_value_sales_submit = fields.Float(
        "6. Total value of sales and all other outputs excluding any VAT. (Includes box 8 figure)",
        (13, 0),
        default=0
    )
    total_value_purchase_submit = fields.Float(
        "7. Total value of purchases and all other inputs excluding any VAT. (Include box 9 figure)",
        (13, 0),
        default=0
    )
    total_value_goods_supplied_submit = fields.Float(
        "8. Total value of all supplies of goods and related costs, excluding any VAT, to other EC Member States",
        (13, 0),
        default=0
    )
    total_acquisitions_submit = fields.Float(
        "9. Total value of all acquisitions of goods and related costs, excluding any VAT, from other EC Member States",
        (13, 0),
        default=0
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
    triggered_onchange= fields.Boolean(string="I confirm and finalise", default=False)

    @api.onchange('select_vat_obligation', 'company_id', 'gov_test_scenario', 'hmrc_configuration')
    def onchange_reset_fields(self):
        self.search([('vat_due_sales_submit', '!=', False)]).write({
            'vat_due_sales_submit': self.default_get(['vat_due_sales_submit'])['vat_due_sales_submit'],
            'vat_due_acquisitions_submit': self.default_get(['vat_due_acquisitions_submit'])['vat_due_acquisitions_submit'],
            'total_vat_due_submit': self.default_get(['total_vat_due_submit'])['total_vat_due_submit'],
            'vat_reclaimed_submit': self.default_get(['vat_reclaimed_submit'])['vat_reclaimed_submit'],
            'net_vat_due_submit': self.default_get(['net_vat_due_submit'])['net_vat_due_submit'],
            'total_value_sales_submit': self.default_get(['total_value_sales_submit'])['total_value_sales_submit'],
            'total_value_purchase_submit': self.default_get(['total_value_purchase_submit'])['total_value_purchase_submit'],
            'total_value_goods_supplied_submit': self.default_get(['total_value_goods_supplied_submit'])['total_value_goods_supplied_submit'],
            'total_acquisitions_submit': self.default_get(['total_acquisitions_submit'])['total_acquisitions_submit'],
        })

        self.vat_due_sales_submit = False
        self.vat_due_acquisitions_submit = False
        self.total_vat_due_submit = False
        self.vat_reclaimed_submit = False
        self.net_vat_due_submit = False
        self.total_value_sales_submit = False
        self.total_value_purchase_submit = False
        self.total_value_goods_supplied_submit = False
        self.total_acquisitions_submit = False

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
            ('date_stop', '=', self.date_to),
            ('company_id', '=', self.company_id.id)
        ])
        context = str({'period_id': retrieve_period.id, \
                                 'fiscalyear_id': retrieve_period.fiscalyear_id.id, \
                                 'state': 'posted'})
        period_code = retrieve_period.code
        name = period_code and (':' + period_code) or ''

        retrieve_vat_code_ids = self.env['account.tax.code'].search([
            ('code', 'in', ['1','2', '3', '4', '5', '6', '7', '8', '9']),('company_id', '=', self.company_id.id)
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
            #HMRC does not take negative value therefore need to change the negative value for Net vat due field
            self.net_vat_due_submit = abs(self.net_vat_due_submit)
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
        token_record = self.env['mtd.api_tokens'].search([
            ('api_id', '=', self.api_id.id),
            ('company_id', '=', self.company_id.id)
        ])
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


