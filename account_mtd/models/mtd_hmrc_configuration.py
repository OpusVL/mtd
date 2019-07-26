# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class MtdHmrcConfiguration(models.Model):
    _name = 'mtd.hmrc_configuration'
    _description = "user parameters to connect to HMRC's MTD API's"

    name = fields.Char(required=True)
    server_token = fields.Char(required=True)
    client_id = fields.Char(required=True)
    client_secret = fields.Char(required=True)
    environment = fields.Selection([
        ('sandbox', ' Sandbox'),
        ('live', ' Live'),
    ],  string="HMRC Environment",
        required=True)
    hmrc_url = fields.Char('HMRC URL', required=True)
    redirect_url = fields.Char('Redirect URL', required=True)
    access_token = fields.Char()
    refresh_token = fields.Char()
    state = fields.Char()
