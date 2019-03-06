# -*- coding: utf-8 -*-

import requests
import json
import logging
import werkzeug

from openerp import models, fields, api, exceptions
from datetime import datetime

_logger = logging.getLogger(__name__)


class MtdIssueRequest(models.Model):
    _name = 'mtd.issue_request'
    _description = "issues connection request step - 3"

    @api.multi
    def json_command(self, command, module_name=None, record_id=None, api_tracker=None, timeout=3):
        try:
            record = self.env[module_name].search([('id', '=', record_id)])
            _logger.info(
                "json_command - we need to find the record and assign it to self"
            )
            token_record = self.env['mtd.api_tokens'].search([
                ('api_id', '=', record.api_id.id),
                ('company_id', '=', record.company_id.id)
            ])
            access_token = token_record.access_token if token_record else ""
            # may not newed next line of code will need to look into this further while testing.
            # refresh_token = token_record.refresh_token if token_record else ""

            header_items = {"Accept": "application/vnd.hmrc.1.0+json"}
            if record.endpoint_name == "application":
                header_items["authorization"] = ("Bearer " + record.hmrc_configuration.server_token)
            elif record.endpoint_name == "user":
                # need to first check if the user has any accessToken and refreshtoken
                # If not we need to proceed to the first and second step and then come to this step.
                header_items["authorization"] = ("Bearer " + str(access_token))

            hmrc_connection_url = "{}{}".format(record.hmrc_configuration.hmrc_url, record.path)
            _logger.info(
                "json_command - hmrc connection url:- {connection_url}, ".format(connection_url=hmrc_connection_url) +
                "headers:- {header}".format(header=header_items)
            )
            response = requests.get(hmrc_connection_url, timeout=timeout, headers=header_items)
            return self.handle_request_response(response, record, hmrc_connection_url, token_record, api_tracker)
        except ValueError:
            api_tracker.closed = 'error'

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
        if response.ok:
            success_message = (
                    "Date {date}     Time {time} \n".format(date=datetime.now().date(),
                                                            time=datetime.now().time())
                    + "Congratulations ! The connection succeeded. \n"
                    + "Please check the log below for details. \n\n"
                    + "Connection Status Details: \n"
                    + "Request Sent: \n{connection_url} \n\n".format(connection_url=url)
                    + "Response Received: \n{message}".format(message=response_token['message'])
            )
            record.response_from_hmrc = success_message
            if api_tracker:
                _logger.info(
                    "json_command - response received ok we have record id so we " +
                    "return werkzeug.utils.redirect "
                )
                _logger.info(
                    "-------Redirect is:- " +
                    "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=module_name) +
                    "menu_id={menu}&action={action}".format(menu=menu_id, action=action)
                )
                return werkzeug.utils.redirect(
                    "/web#id={id}&view_type=form&model={model}&".format(id=record.id, model=module_name) +
                    "menu_id={menu}&action={action}".format(menu=menu_id, action=action)
                )
            return True

        elif (response.status_code == 401 and
              record.endpoint_name == "user" and
              response_token['message'] == "Invalid Authentication information provided"):
            _logger.info(
                "json_command - code 401 found, user button clicked,  " +
                "and message was:- {} ".format(response_token['message'])
            )
            return self.env['mtd.refresh_authorisation'].refresh_user_authorisation(record, api_token_record)

        else:
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
