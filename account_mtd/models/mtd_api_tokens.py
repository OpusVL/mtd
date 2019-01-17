from odoo import models, fields, api

class MtdApiTokens(models.Model):
    _name = 'mtd.api_tokens'
    _description = "api token table"
    
    api_id = fields.Char('API Id', required=True)
    api_name = fields.Char('API Name', required=True)
    authorisation_code = fields.Char('Authorisation Code', required=True)
    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')