# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


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
    redonly_on_live = fields.Boolean(default=False)

    @api.onchange('environment')
    def onchange_environment(self):


        if self.environment == 'live':
            # Note If there are any change to these fields please copy the changes to the create function as well
            self.name = 'HMRC Live Environment'
            self.server_token = '5b9635be5d53d5d87bdcb051ee90e760'
            self.client_id = '4wB_PpdQAn81wCE0usci6_xSzYIa'
            self.client_secret = '44c3ae5a-cbbf-4fa5-a5fc-04c96a10d719'
            self.hmrc_url = 'https://api.service.hmrc.gov.uk/'
            self.redonly_on_live = True

            self.search([('environment', '=', 'live')]).write({
                'name':'HMRC Live Environment'
            })

        else:
            self.name = ''
            self.server_token = ''
            self.client_id = ''
            self.client_secret = ''
            self.hmrc_url = ''
            self.redonly_on_live = False

    def create(self, cr, uid, vals, context=None):
        if vals['environment'] == 'live':
            vals['name'] = 'HMRC Live Environment'
            vals['server_token'] = '5b9635be5d53d5d87bdcb051ee90e760'
            vals['client_id'] = '4wB_PpdQAn81wCE0usci6_xSzYIa'
            vals['client_secret'] = '44c3ae5a-cbbf-4fa5-a5fc-04c96a10d719'
            vals['hmrc_url'] = 'https://api.service.hmrc.gov.uk/'
            vals['redonly_on_live'] = True

        record = super(MtdHmrcConfiguration, self).create(cr, uid, vals=vals, context=context)
        return record

