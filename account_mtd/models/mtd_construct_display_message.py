# -*- coding: utf-8 -*-

from odoo import models
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
        response_errors = []

        requests_received = response_token.get("requests", [])
        if requests_received:
            for header in requests_received[0].get('headers'):
                if header.get('code') == 'INVALID_HEADER':
                    response_errors.append(
                        "{header} : {value}\nError : {error}\nWarning: {warning}\n".format(
                            header=header.get('header'),
                            value=header.get('value'),
                            error=header.get('errors', "[]"),
                            warning=header.get('warning', "[]"),
            ))
            resp_message = '\nPath : {path}\nMethod : {method}\nRequestTimestamp : {time}\nCode : {code}\n\nHeaders: {headers}\n\n'.format(
                path=requests_received[0].get('path'),
                method=requests_received[0].get('method'),
                time=requests_received[0].get('requestTimestamp'),
                code=requests_received[0].get('code'),
                headers='\n'.join(response_errors),
            )
        if resp_error:
            resp_error = "\n{}".format(resp_error)

        error_message = (
                "Date {date}     Time {time} \n".format(date=datetime.now().date(), time=datetime.now().time())
                + "Connection Status Details: \n"
                + "Request Sent: \n{auth_url} \n\n".format(auth_url=url)
                + "Error Code:\n{code} \n\n".format(code=code)
                + "Response Received: {resp_error}\n{message}".format(
            resp_error=resp_error,
            message=resp_message,
        ))

        return error_message
