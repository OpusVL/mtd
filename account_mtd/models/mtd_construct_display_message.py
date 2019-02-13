# -*- coding: utf-8 -*-

from odoo import models
from datetime import datetime


class MtdUserAuthorisation(models.Model):
    _name = 'mtd.display_message'
    _description = "construct error message to doisplay to the user"

    def consturct_error_message_to_display(self, url=None, code=None, message=None, error=None):
        if error:
            error = "\n{}".format(error)
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