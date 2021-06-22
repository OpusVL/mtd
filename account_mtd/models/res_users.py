# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import urllib
import pytz
import uuid
from odoo.http import request
from datetime import datetime

class ResUsers(models.Model):
    _inherit = 'res.users'

    screen_width = fields.Char(
    	string='Screen Width',
    	readonly=True
    )
    screen_height = fields.Char(
    	string='Screen Height',
    	readonly=True
    )
    screen_depth = fields.Char(
    	string='Screen Color Depth',
    	readonly=True
    )
    screen_scale = fields.Char(
    	string='Screen Scalling Factor',
    	readonly=True
    )
    user_agent = fields.Char(
        string='Browser User Agent',
        readonly=True
    )
    browser_plugin = fields.Char(
        string='Browser Plugins',
        readonly=True
    )
    browser_dnt = fields.Boolean(
        string='Browser DNT',
        readonly=True
    )
    client_ip = fields.Char(
        string='Client Ip',
    )
    client_factor_ref = fields.Char(
        string='Client Factor Reference',
        readonly=True
    )
    client_device_id = fields.Char(
        string='Client Device ID'
    )
    client_ip_address = fields.Char(
        string='Client IP Address'
    )
    client_timezone = fields.Char(
        string='Client Timezone'
    )

    def get_user_uuid4(self):
        return str(uuid.uuid4())

    def _get_users_headers(self):
        return {
            "Gov-client-screens" : 'width={screen_width}&height={screen_height}&scaling-factor={screen_scale}&colour-depth={screen_depth}'.format(screen_width=self.screen_width, screen_height=self.screen_height, screen_scale=self.screen_scale, screen_depth=self.screen_depth),
            "Gov-client-window-size" : 'width={screen_width}&height={screen_height}'.format(screen_width=self.screen_width, screen_height=self.screen_height),
            "Gov-Client-Browser-Plugins" : '{browserplugin}'.format(browserplugin= self.browser_plugin),
            "Gov-Client-Browser-JS-User-Agent" : '{useragent}'.format(useragent=self.user_agent),
            "Gov-Client-Browser-Do-Not-Track" : '{browserdnt}'.format(browserdnt=self.browser_dnt).lower(),
            "Gov-Client-Device-Id": '{uuid1}'.format(uuid1=self.client_device_id),
            "Gov-Client-Timezone": self.client_timezone,
            "Gov-client-local-ips": self.client_ip_address,
        }

    def _get_vendor_headers(self, vendor_ip):
        mtd_module = self.env['ir.module.module'].search([('name','=','account_mtd')], limit=1)
        return {
            "Gov-vendor-version":'Odoo%20SA=13.0&moduleversion={version}'.format(version=mtd_module.installed_version),
            # "Gov-vendor-license-ids": urllib.urlencode({'Odoo':'13.0-20201006-community-edition'}),
            "Gov-vendor-public-ip": '{vendorip}'.format(vendorip=vendor_ip),
            "Gov-vendor-forwarded":'by={vendorip}&for={clientip}'.format(vendorip=vendor_ip, clientip=self.client_ip),
            "Gov-Vendor-Product-Name": 'Product%20Odoo',
        }

    def _get_client_headers(self, company):
        iptime_now = str(datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S.%f'))[:-3]
        if not company.hmrc_username:
            raise exceptions.Warning('HMRC UserID Mandatory in Company')
            
        # Multi Factor No need To send in the header
        # if not self.client_factor_ref:
        #     self.write({'client_factor_ref': uuid.uuid4().hex[:13]})
        # multi_factor_now = str(datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%MZ'))
        # multi_factor = {
        #     'type': 'TOTP',
        #     'timestamp': str(multi_factor_now),
        #     'unique-reference': self.client_factor_ref,
        # }
        return {
            "Gov-Client-Connection-Method": 'WEB_APP_VIA_SERVER',
            "Gov-Client-Public-IP": self.client_ip,
            "Gov-Client-Public-Port": '{remoteport}'.format(remoteport=request.httprequest.environ['REMOTE_PORT']),
            "Gov-Client-User-Ids": 'Odoo=opusvl{username}'.format(username=company.hmrc_username),
            "Gov-Client-Local-IPs-Timestamp": str(iptime_now)+ 'Z',
            "Gov-Client-Public-IP-Timestamp": str(iptime_now)+ 'Z',
            # "Gov-client-multi-factor": urllib.urlencode(multi_factor),
        }

