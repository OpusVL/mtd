# -*- coding: utf-8 -*-

from openerp import models
from datetime import datetime


class MtdUserAuthorisation(models.Model):
    _name = 'mtd.display_message'
    _description = "construct error message to doisplay to the user"

    def construct_error_message_to_display(self, url=None, code=None, response_token=None):
        resp_message=''
        resp_error=''
        if 'error_description' in response_token.keys():
            resp_message = response_token['error_description']
        elif 'message' in response_token.keys():
            resp_message = response_token['message']
        if 'error' in response_token.keys():
            resp_error = response_token['error']
        resp_error_message = ""
        if 'errors' in response_token.keys():
            respo_errors = response_token['errors']
            for error in respo_errors:
                error_code = error["code"]
                error_message = error["message"]

                resp_error_message += "\n\nError Code: \n{}\nError Message: \n{}".format(error_code, error_message)

        if resp_error:
            resp_error = "\n{}".format(resp_error)

        error_message = (
                "Date {date}     Time {time} \n".format(date=datetime.now().date(), time=datetime.now().time())
                + "Sorry. The connection failed ! \n"
                + "Please check the log below for details. \n\n"
                + "Connection Status Details: \n"
                + "Request Sent: \n{auth_url} \n\n".format(auth_url=url)
                + "Error Code:\n{code} \n\n".format(code=code)
                + "Response Received: {resp_error}\n{message}{resp_error_message}".format(
            resp_error=resp_error,
            message=resp_message,
            resp_error_message=resp_error_message
        ))

        return error_message
