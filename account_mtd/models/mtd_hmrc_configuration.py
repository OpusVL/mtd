# -*- coding: utf-8 -*-
import json
import requests
import logging
from openerp import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class MtdHmrcConfiguration(models.Model):
    _name = 'mtd.hmrc_configuration'
    _description = "user parameters to connect to HMRC's MTD API's"

    name = fields.Char(required=True)
    client_id = fields.Char(required=True)
    client_secret = fields.Char(required=True)
    environment = fields.Selection([
        ('sandbox', ' Sandbox'),
        ('live', ' Live'),
    ],  string="HMRC Environment",
        required=True)
    hmrc_url = fields.Char('HMRC URL', required=True)
    redirect_url = fields.Char('Redirect URL', required=True)
    vendor_public_ip = fields.Char(
        string='Redirect URL IP Address (Odoo Server)', 
        required=True, 
        help="The public IP address of the server that the originating device sent their requests to."
    )
    access_token = fields.Char()
    refresh_token = fields.Char()
    state = fields.Char()

    @api.one
    def get_access_token(self):
        """
        Access to the VAT Endpoints requires the Bearer token to be derived from an OAuth request.
        When the Endpoint request is being built, this method makes an OAuth request to get the
        token first, which is then used as part of the Endpoint request.
        :return: <str> or <exception>
        """
        client_id = self.client_id
        client_secret = self.client_secret
        url = '{prefix}/oauth/token'.format(
            prefix=self.hmrc_url.rstrip('/')
        )
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        payload = {
            'client_secret': client_secret,
            'client_id': client_id,
            'grant_type': 'client_credentials',
            'scope': 'read:vat write:vat',
        }

        try:
            response = requests.post(url=url, headers=headers, data=payload)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            message = self.format_error(errh)
            _logger.warn(message)
            raise exceptions.Warning(message)
        except requests.exceptions.ConnectionError as errc:
            message = self.format_error(errc)
            _logger.warn(message)
            raise exceptions.Warning(message)
        except requests.exceptions.Timeout as errt:
            message = self.format_error(errt)
            _logger.warn(message)
            raise exceptions.Warning(message)
        except requests.exceptions.RequestException as err:
            message = self.format_error(err)
            _logger.warn(message)
            raise exceptions.Warning(message)
        except Exception as errunk:
            _logger.warn("Unknown exception:", errunk)
            raise exceptions.Warning("Unknown exception:", errunk)

        response_data = response.json()
        access_token = response_data.get('access_token')
        if not access_token:
            raise exceptions.Warning('Access token not received')
        return access_token.encode('utf-8')

    @staticmethod
    def format_error(err):
        content = json.loads(err.response.content)
        name = content.get('error')
        description = content.get('error_description')
        return '[{message}] {name}: {description}'.format(
            message=err.message,
            name=name,
            description=description,
        )
