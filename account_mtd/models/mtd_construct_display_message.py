# -*- coding: utf-8 -*-

from openerp import models
from datetime import datetime


class MtdUserAuthorisation(models.Model):
    _name = 'mtd.display_message'
    _description = "construct error message to doisplay to the user"

    def consturct_error_message_to_display(self, url=None, code=None, response_token=None):
        resp_message=''
        resp_error=''
        if 'error_description' in response_token.keys():
            resp_message = response_token['error_description']
        elif 'message' in response_token.keys():
            resp_message = response_token['message']
        if 'error' in response_token.keys():
            resp_error = response_token['error']
        if resp_error:
            resp_error = "\n{}".format(resp_error)

        error_message = (
                "Date {date}     Time {time} \n".format(date=datetime.now().date(), time=datetime.now().time())
                + "Sorry. The connection failed ! \n"
                + "Please check the log below for details. \n\n"
                + "Connection Status Details: \n"
                + "Request Sent: \n{auth_url} \n\n".format(auth_url=url)
                + "Error Code:\n{code} \n\n".format(code=code)
                + "Response Received: {error}\n{message}".format(error=error, message=message)
        )

        return error_message