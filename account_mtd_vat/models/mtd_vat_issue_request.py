# -*- coding: utf-8 -*-

import requests
import textwrap
import json
import logging
import werkzeug
import urllib
import hashlib

from odoo import models, fields, api, exceptions
from datetime import datetime

_logger = logging.getLogger(__name__)

detailed_submission_list = [
    'statement_id',
    'create_date',
    'company_id',
    'currency_id',
    'date_maturity',
    'partner_id',
    'reconcile_partial_id',
    'blocked',
    'analytic_account_id',
    'create_uid',
    'credit',
    'centralisation',
    'journal_id',
    'reconcile_id',
    'tax_code_id',
    'state',
    'debit',
    'ref',
    'account_id',
    'period_id',
    'write_date',
    'date_created',
    'date',
    'write_uid',
    'move_id',
    'product_id',
    'reconcile_ref',
    'name',
    'tax_amount',
    'account_tax_id',
    'product_uom_id',
    'amount_currency',
    'quantity',
    'unique_number',
    'account_move_line_id'
]


class MtdVatIssueRequest(models.Model):
    _name = 'mtd_vat.issue_request'
    _description = "VAT issues connection request step - 3"

    @api.multi
    def json_command(self, command, module_name=None, record_id=None, api_tracker=None, timeout=3):
        # TODO command not used?
        try:
            # TODO take record (with more descriptive name) as param instead
            #  of module_name and record_id.  Also we can't do anything without
            #  it so no point making the parameter optional
            record = self.env[module_name].search([('id', '=', record_id)])
            _logger.info(
                "json_command - we need to find the record and assign it to self"
            )
            token_record = self.env['mtd.api_tokens'].search([
                ('api_id', '=', record.api_id.id),
                ('company_id', '=', record.company_id.id)
            ])
            access_token = token_record.access_token if token_record else ""
            # may not need next line of code will need to look into this further while testing.
            # refresh_token = token_record.refresh_token if token_record else ""

            header_items = {"Accept": "application/vnd.hmrc.1.0+json"}
            header_items["authorization"] = ("Bearer " + str(access_token))
            header_items["scope"] = record.scope
            header_items["Content-Type"] = "application/json"
            # if record.endpoint_name == "view-vat-returns":
            #     header_items["scope"] = record.scope

            if record.gov_test_scenario:
                header_items["Gov-Test-Scenario"] = record.gov_test_scenario.name

            if record.endpoint_name in ('submit-vat-returns', 'view-vat-returns'):
                date_from = record.select_vat_obligation.start
                date_to = record.select_vat_obligation.end
            else:
                date_from = record.date_from
                date_to = record.date_to

            hmrc_connection_url = "{}{}?from={}&to={}".format(
                record.hmrc_configuration.hmrc_url, record.path, date_from, date_to)

            _logger.info(
                "json_command - hmrc connection url:- {connection_url}, ".format(connection_url=hmrc_connection_url) +
                "headers:- {header}".format(header=header_items)
            )

            if record.endpoint_name == 'submit-vat-returns':
                params = self.build_submit_vat_params(record)
                response = requests.post(
                    hmrc_connection_url,
                    data=json.dumps(params),
                    timeout=timeout,
                    headers=header_items
                )
            else:
                response = requests.get(hmrc_connection_url, timeout=timeout, headers=header_items)
            return self.handle_request_response(response, record, hmrc_connection_url, token_record, api_tracker)

        except ValueError:
            if api_tracker:
                api_tracker.closed = 'error'
            error_message = (
                "Date {date}     Time {time} \n".format(date=datetime.now().date(), time=datetime.now().time())
                + "Sorry. The connection failed ! \n"
                + "Please check the log below for details. \n\n"
                + "Connection Status Details: \n"
                + "Request Sent: \n{auth_url} \n\n".format(auth_url=hmrc_connection_url)
                + "Error Code:\n{code} \n\n".format(code=response.text)
            )
            record.response_from_hmrc = error_message

            if api_tracker:
                return werkzeug.utils.redirect(
                    "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=module_name) +
                    "menu_id={menu}&action={action}".format(menu=api_tracker.menu_id, action=api_tracker.action)
                )
            return True

    def handle_request_response(self, response, record=None, url=None, api_token_record=None, api_tracker=None):
        response_token = json.loads(response.text)

        if api_tracker:
            action = api_tracker.action
            menu_id = api_tracker.menu_id
            module_name = api_tracker.module_name
        _logger.info(
            "json_command - received respponse of the request:- {response}, ".format(response=response) +
            "and its text:- {response_token}".format(response_token=response_token)
        )
        record.show_response_flag = True
        if response.ok:
            record.view_vat_flag = False
            if record.endpoint_name == "vat-obligation":
                self.show_log_button = True
                self.add_obligation_logs(response, record)
            elif record.endpoint_name == "vat-liabilities":
                self.add_liabilities_logs(response, record)
            elif record.endpoint_name == "vat-payments":
                self.add_payments_logs(response, record)
            elif record.endpoint_name == "view-vat-returns":
                record.view_vat_flag = True
                self.display_view_returns(response, record)
            elif record.endpoint_name == "submit-vat-returns":
                record.submit_vat_flag=True
                self.notify_submit_vat_returns_success(endpoint_record=record)
                self.add_submit_vat_returns(response, record)
            return self.process_successful_response(record, api_tracker)

        elif (response.status_code == 401 and
              response_token['message'] == "Invalid Authentication information provided"):

            _logger.info(
                "json_command - code 401 found, user button clicked,  " +
                "and message was:- {} ".format(response_token['message'])
            )
            #record.show_obligation_link = False
            record.view_vat_flag=False
            return self.env['mtd.refresh_authorisation'].refresh_user_authorisation(record, api_token_record)

        else:
            #record.show_obligation_link = False
            record.view_vat_flag = False
            response_token = json.loads(response.text)
            error_message = self.env['mtd.display_message'].construct_error_message_to_display(
                url=url,
                code=response.status_code,
                response_token=response_token
            )
            _logger.info("json_command - other error found:- {error} ".format(error=error_message))
            record.response_from_hmrc = error_message
            if api_tracker:
                return werkzeug.utils.redirect(
                    "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=module_name) +
                    '&menu_id={menu}&action={action}'.format(menu=menu_id, action=action)
                )
            return True

    def process_successful_response(self, record=None, api_tracker=None):
        if api_tracker:
            _logger.info(
                "json_command - response received ok we have record id so we " +
                "return werkzeug.utils.redirect "
            )
            _logger.info(
                "-------Redirect is:- " +
                "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=api_tracker.module_name) +
                "menu_id={menu}&action={action}".format(menu=api_tracker.menu_id, action=api_tracker.action)
            )
            return werkzeug.utils.redirect(
                "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=api_tracker.module_name) +
                "menu_id={menu}&action={action}".format(menu=api_tracker.menu_id, action=api_tracker.action)
            )
        return True

    def add_liabilities_logs(self, response=None, record=None):
        response_logs = json.loads(response.text)
        logs = response_logs['liabilities']

        display_message = ""
        for log in logs:
            tax_periods = log['taxPeriod']
            display_message += ("\nFrom:- {from_date}\nTo:- {to}\n".format(
                from_date=tax_periods['from'],
                to=tax_periods['to'])
            )
            display_message += ("Type:- {type}\nDue On:- {due}\n".format(type=log["type"], due=log["due"]) +
                "Amount Outstanding:- {outstanding}\nOriginal Amount:- {original}\n".format(
                    outstanding=log["outstandingAmount"],
                    original=log["originalAmount"])
            )

        success_message = (
                "Date {date}     Time {time} \n".format(date=datetime.now().date(),
                                                        time=datetime.now().time())
                + "Congratulations ! The connection succeeded. \n"
                + "Please check the response below.\n\n {message}".format(message=display_message)
        )
        record.response_from_hmrc = success_message

    def notify_submit_vat_returns_success(self, endpoint_record):
        endpoint_record.select_vat_obligation\
            .have_sent_submission_successfully = True
        self.env.cr.commit()   # Make sure crash later doesn't lose this status

    def add_submit_vat_returns(self, response=None, record=None):
        response_logs = json.loads(response.text)
        submission_log = self.create_submission_log_entry(response.text, record)
        # Make sure crash later doesn't wipe out the submission log entry
        self.env.cr.commit()
        record.response_from_hmrc = self._success_message(
            submission_log_entry=submission_log,
            current_time=datetime.now(),
        )
        self.copy_account_move_lines_to_storage(record, response_logs['formBundleNumber'], submission_log)

    @api.model
    def _success_message(self, submission_log_entry, current_time):
        template = """
            Date {date}     Time {time}
            
            Congratulations ! The submission has been made successfully to HMRC.
            
            Period: {log.start} - {log.end}
            Unique number: {log.unique_number}
            Payment indicator: {log.payment_indicator}
            Charge ref number: {log.charge_ref_number}
            Processing date: {log.raw_processing_date}
            Please check the submission logs for details.
            """
        stripped_template = textwrap.dedent(template).strip()
        return stripped_template.format(
            log=submission_log_entry,
            time=current_time.time(),
            date=current_time.date(),
        )

    @api.model
    def create_submission_log_entry(self, response_text, record):
        return self.env['mtd_vat.vat_submission_logs'].create({
            'name': "{} - {}".format(record.date_from, record.date_to),
            'response_text': response_text,
            'start': record.date_from,
            'end': record.date_to,
            'submission_status': "Successful",
            'vrn': record.vrn,
            'vat_due_sales_submit': record.vat_due_sales_submit,
            'vat_due_acquisitions_submit': record.vat_due_acquisitions_submit,
            'total_vat_due_submit': record.total_vat_due_submit,
            'vat_reclaimed_submit': record.vat_reclaimed_submit,
            'net_vat_due_submit': record.net_vat_due_submit,
            'total_value_sales_submit': record.total_value_sales_submit,
            'total_value_purchase_submit': record.total_value_purchase_submit,
            'total_value_goods_supplied_submit': record.total_value_goods_supplied_submit,
            'total_acquisitions_submit': record.total_acquisitions_submit,
            'company_id': record.company_id.id,
            'redirect_url': record.hmrc_configuration.redirect_url
        })

    def copy_account_move_lines_to_storage(self, record, unique_number, submission_log):

        journal_item_ids = self.env['mtd_vat.vat_endpoints'].get_journal_item_ids_from_calculation_table(
            record.date_from,
            record.date_to,
            record.company_id
        )
        move_lines_to_copy = self.env['account.move.line'].search([
            ('id', 'in', journal_item_ids)])

        storage_model = self.env['mtd_vat.vat_detailed_submission_logs']
        move_lines_to_copy_list = move_lines_to_copy.read()
        for move_line in move_lines_to_copy_list:
            amended_move_line = move_line.copy()
            amended_move_line['account_move_line_id'] = move_line.get('id')
            amended_move_line['unique_number'] = unique_number
            for k, v in move_line.items():
                if type(v) == tuple:
                    amended_move_line[k] = v[0]  # Handle Many2ones

            stored_record = storage_model.search([('account_move_line_id', '=', move_line.get('id'))])
            if not stored_record:
                storage_model.create(amended_move_line)

        self.set_vat_for_account_move_line(move_lines_to_copy, unique_number, submission_log)

        # create journal records and then reconcile records
        self.create_journal_record_for_submission(move_lines_to_copy, record, submission_log)

        #get md5 hash value
        hash_object = self.get_hash_object_for_submission(unique_number, record.company_id.id)

    def set_vat_for_account_move_line(self, account_move_lines, unique_number, submission_log):

        for line in account_move_lines:
            line.vat=True
            line.vat_submission_id = submission_log.id
            line.unique_number = unique_number

    def add_payments_logs(self, response=None, record=None):
        response_logs = json.loads(response.text)
        payment_flag = True
        logs = response_logs['payments']

        display_message = ''
        for log in logs:
            received = ""
            if 'received' in log.keys():
                received = "Received:- {}".format(log["received"])

            display_message += "Amount:- {}\n{}\n\n".format(log["amount"], received)

        success_message = (
                "Date {date}     Time {time} \n".format(date=datetime.now().date(),
                                                        time=datetime.now().time())
                + "Congratulations ! The connection succeeded. \n"
                + "Please check the response below.\n\n{message}".format(message=display_message)
        )
        record.response_from_hmrc = success_message
        record.show_response_flag = True

    def add_obligation_logs(self, response=None, record=None):

        # retrieve action and menu id so we can provide a link to the obligation view.
        record.obligation_log_action = self.env.ref('account_mtd_vat.action_mtd_vat_obligation_log')
        record.obligation_log_menu = self.env.ref('account_mtd_vat.submenu_mtd_vat_obligation_log')

        response_logs = json.loads(response.text)
        logs = response_logs['obligations']
        obligation_message = ""
        for log in logs:
            received = ""
            if 'received' in log.keys():
                received = log['received']

            obligation_logs = self.env['mtd_vat.vat_obligations_logs'].search([
                ('start', '=', log['start']),
                ('end', '=', log['end']),
                ('company_id', '=', record.company_id.id)
            ])
            obligation_message += (
                "Period: {}\n".format(log["start"], log["end"])
                + "Start: {}\n" .format(log['start'])
                + "End: {}\n".format(log['end'])
                + "Period Key: {}\n".format(log['periodKey'])
                + "Status: {}\n".format(log['status'])
                + "Received: {}\n".format(received)
                + "Due: {}\n\n".format(log['due'])
            )
            self.update_write_obligation(log, received, obligation_logs, record)

        success_message = (
            "Date {date}     Time {time} \n\n{obligations}".format(date=datetime.now().date(),
                                                        time=datetime.now().time(),
                                                        obligations=obligation_message)
        )
        #record.show_obligation_link = True

        record.response_from_hmrc = success_message
        record.show_response_flag = True
        record.obligation_log_link = "Please check the VAT logs here"

    def update_write_obligation(self, log, received, obligation_logs, record):
        if obligation_logs:
            obligation_logs.name = "{} - {}".format(log["start"], log["end"]),
            obligation_logs.start = log['start']
            obligation_logs.end = log['end']
            obligation_logs.period_key = log['periodKey']
            obligation_logs.status = log['status']
            obligation_logs.received = received
            obligation_logs.due = log['due']
            obligation_logs.company_id = record.company_id.id
            obligation_logs.vrn = record.vrn
        else:
            obligation_logs = obligation_logs.create({
                'name': "{} - {}".format(log["start"], log["end"]),
                'start': log['start'],
                'end': log['end'],
                'period_key': log['periodKey'],
                'status': log['status'],
                'received': received,
                'due': log['due'],
                'company_id': record.company_id.id,
                'vrn': record.vrn
            })

    def display_view_returns(self, response, record):
        response_logs = json.loads(response.text)
        record.period_key = response_logs['periodKey']
        record.vat_due_sales = response_logs['vatDueSales']
        record.vat_due_acquisitions = response_logs['vatDueAcquisitions']
        record.total_vat_due = response_logs['totalVatDue']
        record.vat_reclaimed = response_logs['vatReclaimedCurrPeriod']
        record.net_vat_due = response_logs['netVatDue']
        record.total_value_sales = response_logs['totalValueSalesExVAT']
        record.total_value_purchase = response_logs['totalValuePurchasesExVAT']
        record.total_value_goods_supplied = response_logs['totalValueGoodsSuppliedExVAT']
        record.total_acquisitions = response_logs['totalAcquisitionsExVAT']

    def build_submit_vat_params(self, record):
        return {
            "periodKey": urllib.parse.quote_plus(record.period_key_submit),
            "vatDueSales": record.vat_due_sales_submit,
            "vatDueAcquisitions": record.vat_due_acquisitions_submit,
            "totalVatDue": record.total_vat_due_submit,
            "vatReclaimedCurrPeriod": record.vat_reclaimed_submit,
            "netVatDue": abs(record.net_vat_due_submit),
            "totalValueSalesExVAT": record.total_value_sales_submit,
            "totalValuePurchasesExVAT": record.total_value_purchase_submit,
            "totalValueGoodsSuppliedExVAT": record.total_value_goods_supplied_submit,
            "totalAcquisitionsExVAT": record.total_acquisitions_submit,
            "finalised": record.finalise
        }

    def get_hash_object_for_submission(self, unique_number, company_id):

        # get unique ref no and based on that get all general items for that unique ref no
        # loop through the journal items make it into a string and then get the md5 no  and then store it in the
        # detailed submission logs and in accounts journal items

        journal_items_for_integrity = self.env['mtd_vat.vat_detailed_submission_logs'].search([
            ('unique_number', '=', unique_number)
        ])

        #get the md5 value for the last submission of the company and remove the record with current unique number
        submission_log_md5_value = self.env['mtd_vat.vat_submission_logs'].search(
            [('company_id', '=', company_id), ('unique_number', '!=', unique_number)],
            order="id desc",
            limit=1).md5_integrity_value

        journal_entry_dict = {}
        journal_entry_list = []
        if journal_items_for_integrity:
            # update the previousmd5 valueto the list
            journal_entry_list.append(submission_log_md5_value)
            for record in journal_items_for_integrity:
                record_id = record.id
                for field in detailed_submission_list:
                    journal_entry_list.append(record[field])

                journal_entry_dict[record_id] = journal_entry_list

            hash_value = hashlib.md5(str(journal_entry_dict).encode('utf-8'))

            # update the hash value in the detailed submission table
            for record in journal_items_for_integrity:
                record.md5_integrity_value = hash_value.hexdigest()

            # get the submission record and update the submission record with the md5 value
            submission_log_record = self.env['mtd_vat.vat_submission_logs'].search([
                ('unique_number', '=', unique_number)
            ])
            submission_log_record.md5_integrity_value = hash_value.hexdigest()

    def create_journal_record_for_submission(self, move_lines_to_copy, record, submission_log):

        account_move = self.env['account.move']
        hmrc_posting_config = self.env['mtd_vat.hmrc_posting_configuration'].search([
            ('name', '=', record.company_id.id)])

        account_move_id = account_move.create({
            'name': 'HMRC VAT Submission',
            'ref': 'HMRC VAT Submission',
            'date': submission_log.processing_date,
            'journal_id': hmrc_posting_config.journal_id.id
        })

        move_line_ids = []
        # create account move line entry for tax input account (purchase)
        # 1 workout figures for output moveline
        # box 4 - box2
        input_value = (record.vat_reclaimed_submit - record.vat_due_acquisitions_submit)

        # 2 workout whether to debit or credit?
        input_credit_debit = 'credit'
        if input_value < 0:
            input_credit_debit = 'debit'

        # 2 create input move line
        input_move_line = self.create_account_move_line(
            submission_log.processing_date,
            hmrc_posting_config.input_account.id,
            input_credit_debit,
            input_value,
            account_move_id.id)
        move_line_ids.append(input_move_line.id)

        # create account move line entry for tax output  account (sales)
        # use box1 for value
        # 1 work out whether to debit or credit?
        output_credit_debit = 'debit'
        if record.vat_due_sales_submit < 0:
            output_credit_debit = 'credit'

        # 2 create output move line
        output_move_line = self.create_account_move_line(
            submission_log.processing_date,
            hmrc_posting_config.output_account.id,
            output_credit_debit,
            record.vat_due_sales_submit,
            account_move_id.id)
        move_line_ids.append(output_move_line.id)

        # create account move line entry for HMRC liability Account
        # if record.net_vat_due_submit < 0:
        # can not use the above field to work out the credit and debit as we are using the
        # abs on the field in the first place
        debit_credit_type = "credit"
        if (record.total_vat_due_submit - record.vat_reclaimed_submit) < 0:
            debit_credit_type = "debit"

        liability_move_line = self.create_account_move_line(
            submission_log.processing_date,
            hmrc_posting_config.liability_account.id,
            debit_credit_type,
            abs(record.net_vat_due_submit),
            account_move_id.id)
        move_line_ids.append(liability_move_line.id)

        # Validate the account once the journal items have been created.
        account_move_id._post_validate()
        # update the state of Journal entry to posted.
        account_move_id.state = 'posted'

        # Reconcile Input tax Records
        self.autoreconcile_tax_records(
            hmrc_posting_config.input_account.id,
            input_move_line,
            move_lines_to_copy,
            # period_id.id
        )

        # Reconcile Output tax Records
        self.autoreconcile_tax_records(
            hmrc_posting_config.output_account.id,
            output_move_line,
            move_lines_to_copy,
            # period_id.id
        )

    def create_account_move_line(self, processing_date, account_id, debit_credit_type, value, account_move_id):

        account_move_line = self.env['account.move.line']
        move_line_id = account_move_line.with_context(check_move_validity=False).create({
            'name': 'HMRC VAT Submission',
            'ref': 'HMRC VAT Submission',
            'date': processing_date.date(),
            'account_id': account_id,
            '{}'.format(debit_credit_type): value,
            'move_id': account_move_id
        })
        # 'move_id': account_move_id
        return move_line_id

    # _check_reconcile_validity that checks if account are set as reconciled is outside base function
    # auto_reconcile_lines and check_full_reconcile, so no need to change the base functions
    def autoreconcile_tax_records(self, account_id, move_line_id, move_lines_for_period):
        move_line_account_id = []
        move_line_account_id.append(move_line_id.id)

        for line in move_lines_for_period:
            if line.account_id.id == account_id:
                move_line_account_id.append(line.id)
        account_move_line_obj = self.env['account.move.line']
        line_ids = account_move_line_obj.search([('id', 'in', move_line_account_id)])
        line_ids.auto_reconcile_lines()
        line_ids.check_full_reconcile()


class RetrievePeriodId(models.Model):
    _name = 'mtd_vat.retrieve_period_id'


    def retrieve_period(self, record):
        period = self.env['account.period'].search([
            ('date_start', '=', record.date_from),
            ('date_stop', '=', record.date_to),
            ('company_id', '=', record.company_id.id),
            ('state', '=', 'draft')
        ])

        if record.previous_period == 'no':
            retrieve_period=[]
            retrieve_period.append(period.id)
        else:
            cutoff_date_rec = self.env['mtd_vat.hmrc_posting_configuration'].search([('name', '=', record.company_id.id)])

            all_periods_before_cutoff = self.env['account.period'].search([
                ('date_start', '>=', cutoff_date_rec.cutoff_date.date_start),
                ('state', '=', 'draft'),
                ('company_id', '=', record.company_id.id)
            ])

            all_period_ids = []
            for period in all_periods_before_cutoff:
                all_period_ids.append(period.id)

            retrieve_periods = self.env['account.period'].search([
                ('id', 'in', tuple(all_period_ids)),
                ('date_start', '<=', record.date_from)
            ])

            retrieve_period = []
            for period in retrieve_periods:
                retrieve_period.append(period.id)

        return period, retrieve_period
