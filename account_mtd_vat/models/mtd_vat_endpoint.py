# -*- coding: utf-8 -*-
import logging
import urllib
import re

from openerp import models, fields, api, exceptions
from datetime import datetime, timedelta

from ..hmrc_vat import Box
from ..dictutils import map_keys, restrict_with_fill_values

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
    vrn = fields.Char(related="company_id.vat", string="VAT Number", readonly=True)

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.vrn = self.company_id.vat

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    status = fields.Selection([
        ('o', ' O'),
        ('f', ' F'),
    ])
    gov_test_scenario = fields.Many2one('gov.test.scenario', string='Gov-Test-Scenario')
    x_correlation_id = fields.Char('X-CorrelationId')
    response_from_hmrc = fields.Text(string="Response from HMRC", readonly=True, default="")
    path = fields.Char(string="sandbox_url")
    endpoint_name = fields.Char(string="which_button")
    select_vat_obligation = fields.Many2one(comodel_name='mtd_vat.vat_obligations_logs', default="")
    # retrieve_vat_obligation_first = fields.Many2one(
    #     comodel_name='mtd_vat.vat_endpoints',
    #     compute='_compute_retrieve_vat_obligation_rec')
    obligation_status = fields.Char(compute="_compute_obligation_status_company")
    obligation_company = fields.Integer(compute="_compute_obligation_status_company")
    show_obligation_log_button = fields.Boolean(default=True)
    # obligation_link = fields.Char(related='select_vat_obligation.name')
    # show_obligation_link = fields.Boolean(default=False)

    # @api.depends('name')
    # def _compute_retrieve_vat_obligation_rec(self):
    #     if self.name == 'Submit VAT Returns':
    #         obligation_obj = self.env['mtd_vat.vat_endpoints'].search([
    #             ('name', '=', 'Retrieve VAT Obligations')
    #         ])
    #         self.retrieve_vat_obligation_first = obligation_obj.id

    @api.depends('company_id', 'name')
    def _compute_obligation_status_company(self):
        self.obligation_company = self.company_id.id
        if self.name in ('View VAT Returns', 'Submit a VAT Return'):
            self.obligation_status = 'O' if self.name == 'Submit a VAT Return' else 'F'

        self.env['mtd_vat.vat_obligations_logs'].search([
            ('status', '=', self.obligation_status),
            ('company_id', '=', self.obligation_company)])

    @api.onchange('select_vat_obligation')
    def onchange_date_for_vat_returns(self):
        self.date_from = self.select_vat_obligation.start
        self.date_to = self.select_vat_obligation.end

    # Fields for Viewing the vat returns
    # need to display the result in the field rather than in a Text field
    view_vat_flag = fields.Boolean(default=False)
    period_key = fields.Char(related='select_vat_obligation.period_key', readonly=True)
    vat_due_sales = fields.Float("1. VAT due in this period on sales and other outputs",
        (13, 2),
        readonly=True,
        default=0.00
    )
    vat_due_acquisitions = fields.Float(
        "2. VAT due in this period on acquisitions from other EC Member States",
        (13, 2),
        readonly=True,
        default=0.00
    )
    total_vat_due = fields.Float("3. Total VAT due (the sum of boxes 1 and 2)", (13, 2), readonly=True, default=0.00)
    vat_reclaimed = fields.Float(
        "4. VAT reclaimed in this period on purchases and other inputs (including acquisitions from the EC)",
        (13, 2),
        readonly=True,
        default=0.00
    )
    net_vat_due = fields.Float(
        "5. Net VAT to be paid to HMRC or reclaimed by you (Difference between boxes 3 and 4)",
        (11, 2),
        readonly=True,
        default=0.00
    )
    total_value_sales = fields.Float(
        "6. Total value of sales and all other outputs excluding any VAT. (Includes box 8 figure)",
        (13, 0),
        readonly=True,
        default=0
    )
    total_value_purchase = fields.Float(
        "7. Total value of purchases and all other inputs excluding any VAT. (Include box 9 figure)",
        (13, 0),
        readonly=True,
        default=0
    )
    total_value_goods_supplied = fields.Float(
        "8. Total value of all supplies of goods and related costs, excluding any VAT, to other EC Member States",
        (13, 0),
        readonly=True,
        default=0
    )
    total_acquisitions = fields.Float(
        "9. Total value of all acquisitions of goods and related costs, excluding any VAT, from other EC Member States",
        (13, 0),
        readonly=True,
        default=0
    )

    # submit vat fields
    submit_vat_flag = fields.Boolean(default=False)
    submit_vat_ok_response = fields.Boolean(default=False)
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
    business_declaration = fields.Char(
        readonly=True,
        default=(
            "When you submit this VAT information you are making a legal declaration "
            + "\nthat the information is true and complete. "
            + "\nA false declaration can result in prosecution.")
    )
    agent_declaration = fields.Char(
        readonly=True,
        default=(
            "I confirm that my client has received a copy of the information contained "
            + "\nin this return and approved the information as being correct and "
            + "\ncomplete to the best of their knowledge and belief.")
    )
    review_text = fields.Char(
        readonly=True,
        default=(
            "Please review your VAT summary above. When you are satisfied it is correct, tick 'I confirm and finalise' "
            + "and then click 'Submit a VAT Return.")
    )
    finalise = fields.Boolean(string="I confirm and finalise", default=False)
    triggered_onchange = fields.Boolean(string="I confirm and finalise", default=False)
    previous_period = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],
        'Include Transaction of Previous period',
        required=True,
        default='yes')
    show_response_flag = fields.Boolean(default=False)

    @api.onchange('company_id', 'gov_test_scenario', 'hmrc_configuration')
    def onchange_reset_vat_obligation(self):
        if self.name in ("Submit a VAT Return", "View VAT Returns"):
            self.select_vat_obligation = ""

    @api.onchange('select_vat_obligation', 'company_id', 'gov_test_scenario', 'hmrc_configuration')
    def onchange_reset_fields(self):
        self.submit_vat_flag = False
        self.view_vat_flag = False
        self.submit_vat_ok_response = False
        self.finalise = False
        self.show_response_flag = False

        self.search([('response_from_hmrc', '!=', False)]).write({
            'response_from_hmrc': self.default_get(['response_from_hmrc'])['response_from_hmrc']
        })

        self.response_from_hmrc = ""

        if self.name == "Submit a VAT Return":
            self.reset_vat_submission_values()

        elif self.name == "View VAT Returns":
            self.reset_view_vat_returns_values()

    @api.multi
    def action_vat_connection(self):
        if not self.hmrc_configuration:
            raise exceptions.Warning("Please select HMRC configuration before continuing!")
        elif not self.vrn:
            raise exceptions.Warning("Please enter the VRN")
        elif not self.company_id:
            raise exceptions.Warning("Please select a company before continuing!")
        if self.name in ("Submit a VAT Return", "View VAT Returns") and not self.select_vat_obligation:
            raise exceptions.Warning("Please select a VAT Obligation")

        endpoint_record = self.env['ir.model.data'].search([
            ('res_id', '=', self.id),
            ('model', '=', 'mtd_vat.vat_endpoints')
        ])

        if endpoint_record.name == "mtd_vat_submit_returns_endpoint":
            if not self.select_vat_obligation:
                raise exceptions.Warning("Please select a vat obligation to submit a return")

        self.show_response_flag = False
        self.submit_vat_ok_response = False
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
    def action_vat_breakdown(self, *args):

        # Create on account.tax.chart, with period_id set to ^, and target_move set to either 'posted', or 'all'
        # i.e wizard_rec = self.env['account.tax.chart'].create(<values>)
        # call account_tax_chart_open_window() <-- This will give us a dictionary which by returning
        # - will take us to the chart of taxes
        # i.e chart_of_taxes_view = wizard_rec.account_tax_chart_open_window()
        # {'view_id': x, 'target': 'new', 'context': {'default_company_id': <company_you_want>}}
        wizard_rec = self.env['account.tax.chart'].create(dict(
            date_from=self.date_from,
            date_to=self.date_to,
            target_move='posted',
            previous_period=self.previous_period,
            vat_posted='posted' if self.submit_vat_ok_response else 'unposted',
            company_id=self.company_id.id))

        chart_of_taxes_view = wizard_rec.account_tax_chart_open_window()
        chart_of_taxes_view['target'] = 'new'

        return chart_of_taxes_view

    @api.multi
    def action_retrieve_vat(self, *args):

        if not self.company_id:
            raise exceptions.Warning("Please select a company before continuing!")

        # RESET FOLLOWING FIELDS SO THAT USER CAN VERIFY THESE ONCE vat HAS BEEN RETRIEVED
        self.client_type = ""
        self.finalise = False
        self.response_from_hmrc = ""
        self.show_response_flag = False

        retrieve_period, period_ids, fiscalyear_ids, cutoff_date = self.retrieve_period_and_fiscalyear()
        date_from = self.date_from
        if cutoff_date:
            date_from = cutoff_date

        context = str({
            'period_id': period_ids,
            'fiscalyear_id': fiscalyear_ids,
            'state': 'posted',
            'vat': 'unposted'})

        retrieve_vat_code_ids = self.env['account.tax.code'].search([
            ('code', 'in', list(Box.all_box_codes())),
            ('company_id', '=', self.company_id.id)
        ])
        name = 'Calculated VAT'

        sums_for_tax_code_ids = (
            retrieve_vat_code_ids
            .with_context(
                date_from=date_from,
                date_to=self.date_to,
                period_id=period_ids,
                fiscalyear_id=fiscalyear_ids,
                state='posted',
                vat='unposted',
                company_id=self.company_id.id,
            )
            ._sum_period(name, context)
        )

        def tax_code_id_to_box_code(tax_code_id):
            return retrieve_vat_code_ids\
                .filtered(lambda c: c.id == tax_code_id)\
                .code

        # _sum_period doesn't always return all boxes, and the ones it does
        #  are account.tax.code ids not the box codes themselves
        base_box_sums = restrict_with_fill_values(
            map_keys(tax_code_id_to_box_code, sums_for_tax_code_ids),
            wanted_keys=(Box.all_box_codes() - Box.computed_box_codes()),
            fill_value=0,
        )
        box_values = Box.compute_all(base_box_sums)
        field_box_map = {
            'vat_due_sales_submit': Box.VAT_DUE_SALES,
            'vat_due_acquisitions_submit': Box.VAT_DUE_ACQUISITIONS,
            'total_vat_due_submit': Box.TOTAL_VAT_DUE,
            'vat_reclaimed_submit': Box.VAT_RECLAIMED_ON_INPUTS,
            'net_vat_due_submit': Box.NET_VAT_DUE,
            'total_value_sales_submit': Box.TOTAL_VALUE_SALES,
            'total_value_purchase_submit': Box.TOTAL_VALUE_PURCHASES,
            'total_value_goods_supplied_submit': Box.TOTAL_VALUE_GOODS_SUPPLIED,
            'total_acquisitions_submit': Box.TOTAL_VALUE_ACQUISITIONS,
        }
        if len(retrieve_period) > 0:
            # TODO this if doesn't encompass everything it should
            self.submit_vat_flag = True
            self.update({
                field: box_values[boxcode]
                for (field, boxcode) in field_box_map.items()
            })
        else:
            self.submit_vat_flag = False
            self.show_response_flag = True
            self.response_from_hmrc = (
                "No period matching to the vat obligation found Please try a different period."
            )

    def retrieve_period_and_fiscalyear(self):
        retrieve_period = self.env['account.period'].search([
            ('date_start', '<=', self.date_to),
            ('date_stop', '>=', self.date_to),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'draft')
        ])
        period_ids = [retrieve_period.id]
        fiscalyear_ids = [retrieve_period.fiscalyear_id.id]

        cutoff_date = None
        if self.previous_period == 'yes':
            cutoff_date_rec = self.env['mtd_vat.hmrc_posting_configuration'].search([('name', '=', self.company_id.id)])

            for rec in cutoff_date_rec:
                cutoff_date = rec.cutoff_date

        return retrieve_period, period_ids, fiscalyear_ids, cutoff_date

    def _handle_vat_obligations_endpoint(self):
        vrn = self.get_vrn(self.vrn)
        self.path = "/organisations/vat/{vrn}/obligations".format(vrn=vrn)
        self.endpoint_name = "vat-obligation"
        _logger.info(self.connection_button_clicked_log_message())

        return self.process_connection()

    def _handle_vat_liabilities_endpoint(self):
        vrn = self.get_vrn(self.vrn)
        self.path = "/organisations/vat/{vrn}/liabilities".format(vrn=vrn)
        self.endpoint_name = "vat-liabilities"

        return self.process_connection()

    def _handle_vat_payments_endpoint(self):
        vrn = self.get_vrn(self.vrn)
        self.path = "/organisations/vat/{vrn}/payments".format(vrn=vrn)
        self.endpoint_name = "vat-payments"

        return self.process_connection()

    def _handle_vat_returns_view_endpoint(self):
        vrn = self.get_vrn(self.vrn)
        period_key = urllib.quote_plus(self.select_vat_obligation.period_key)
        self.path = "/organisations/vat/{vrn}/returns/{key}".format(vrn=vrn, key=period_key)
        self.endpoint_name = "view-vat-returns"

        return self.process_connection()

    def _obligation_fulfilled(self):
        # TODO resync with HMRC first
        return self.select_vat_obligation.is_fulfilled()

    def _we_think_we_have_previously_submitted_successfully(self):
        # Because HMRC, at least on the sandbox, doesn't return back the
        # right obligation status on the obligations endpoint after submitting.
        return self.select_vat_obligation.have_sent_submission_successfully

    def _handle_vat_submit_returns_endpoint(self):
        if self._obligation_fulfilled() \
                or self._we_think_we_have_previously_submitted_successfully():
            raise exceptions.Warning(
                "VAT return has already been submitted for this obligation."
            )
        hmrc_posting_template_for_company = (
            self.env['mtd_vat.hmrc_posting_configuration']
            .search([('name', '=', self.company_id.id)])
        )
        if not hmrc_posting_template_for_company:
            raise exceptions.Warning(
                "Chart of Taxes can not be generated!\n " +
                "Please create HMRC Posting Template record first"
            )
        vrn = self.get_vrn(self.vrn)
        self.path = "/organisations/vat/{vrn}/returns".format(vrn=vrn)
        self.endpoint_name = "submit-vat-returns"
        return self.process_connection()

    def get_vrn(self, vrn):
        # strip any space
        strip_vrn = vrn.replace(" ", "")
        split_vrn = re.findall('\d+|\D+', strip_vrn)

        return split_vrn[1]

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

    @api.one
    def handle_user_authorisation_error(self, record):
        # The user authorisation failed therfore we need to handle the display of the response by setting the flags
        # so that the response is displaed tot he user.
        record.show_response_flag = True
        record.view_vat_flag = False

    def connection_button_clicked_log_message(self):
        return "Connection button Clicked - endpoint name {name}, redirect URL:- {redirect}, Path url:- {path}".format(
                name=self.name,
                redirect=self.hmrc_configuration.redirect_url,
                path=self.path
            )

    @api.multi
    def action_go_to_obligation_logs(self, *args):
        obligation_log_action = self.env.ref('account_mtd_vat.action_mtd_vat_obligation_log').id
        obligation_log_menu = self.env.ref('account_mtd_vat.submenu_mtd_vat_obligation_log').id

        redirect_url = self.hmrc_configuration.redirect_url.replace(" ", "")
        redirect_url += (
            "/web?#page=0&limit=80&view_type=list&model=mtd_vat.vat_obligations_logs"
            +"&menu_id={menu}&action={action}".format(
                menu=obligation_log_menu,
                action=obligation_log_action
            )
        )

        return {'url': redirect_url, 'type': 'ir.actions.act_url', 'target': 'new'}

    @api.multi
    def action_submission_log_view(self, *args):
        submission_log_action = self.env.ref('account_mtd_vat.action_mtd_vat_submission_log').id
        submission_log_menu = self.env.ref('account_mtd_vat.submenu_mtd_vat_submission_log').id

        redirect_url = self.hmrc_configuration.redirect_url.replace(" ", "")
        redirect_url += (
            "/web?#page=0&limit=80&view_type=list&model=mtd_vat.vat_obligations_logs"
            +"&menu_id={menu}&action={action}".format(
                menu=submission_log_menu,
                action=submission_log_action
            )
        )

        return {'url': redirect_url, 'type': 'ir.actions.act_url', 'target': 'new'}

    def reset_vat_submission_values(self):
        self.search([('vat_due_sales_submit', '!=', False)]).write({
            'vat_due_sales_submit': self.default_get(['vat_due_sales_submit'])['vat_due_sales_submit'],
            'vat_due_acquisitions_submit': self.default_get(
                ['vat_due_acquisitions_submit'])[
                'vat_due_acquisitions_submit'],
            'total_vat_due_submit': self.default_get(['total_vat_due_submit'])['total_vat_due_submit'],
            'vat_reclaimed_submit': self.default_get(['vat_reclaimed_submit'])['vat_reclaimed_submit'],
            'net_vat_due_submit': self.default_get(['net_vat_due_submit'])['net_vat_due_submit'],
            'total_value_sales_submit': self.default_get(['total_value_sales_submit'])['total_value_sales_submit'],
            'total_value_purchase_submit': self.default_get(
                ['total_value_purchase_submit'])[
                'total_value_purchase_submit'],
            'total_value_goods_supplied_submit': self.default_get(
                ['total_value_goods_supplied_submit'])[
                'total_value_goods_supplied_submit'],
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

    def reset_view_vat_returns_values(self):
        self.view_vat_flag = False
        self.search([('vat_due_sales', '!=', False)]).write({
            'vat_due_sales': self.default_get(['vat_due_sales'])['vat_due_sales'],
            'vat_due_acquisitions': self.default_get(['vat_due_acquisitions'])['vat_due_acquisitions'],
            'total_vat_due': self.default_get(['total_vat_due'])['total_vat_due'],
            'vat_reclaimed': self.default_get(['vat_reclaimed'])['vat_reclaimed'],
            'net_vat_due': self.default_get(['net_vat_due'])['net_vat_due'],
            'total_value_sales': self.default_get(['total_value_sales'])['total_value_sales'],
            'total_value_purchase': self.default_get(['total_value_purchase'])['total_value_purchase'],
            'total_value_goods_supplied': self.default_get(['total_value_goods_supplied'])['total_value_goods_supplied'],
            'total_acquisitions': self.default_get(['total_acquisitions'])['total_acquisitions'],
        })

        self.vat_due_sales = False
        self.vat_due_acquisitions = False
        self.total_vat_due = False
        self.vat_reclaimed = False
        self.net_vat_due = False
        self.total_value_sales = False
        self.total_value_purchase = False
        self.total_value_goods_supplied = False
        self.total_acquisitions = False
