# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class MtdHmrcConfiguration(models.Model):
    _name = 'mtd.hmrc_configuration'
    _description = "user parameters to connect to HMRC's MTD API's"

    name = fields.Char('Name', required=True)
    server_token = fields.Char('Server Token', required=True)
    client_id = fields.Char('Client ID', required=True)
    client_secret = fields.Char('Client Secret', required=True)
    environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('live', 'Live'),
    ],  string="HMRC Environment",
        required=True)
    hmrc_url = fields.Char('HMRC URL', required=True)
    redirect_url = fields.Char('Redirect URL', required=True)
    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')
    state = fields.Char('State')