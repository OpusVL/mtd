# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import urllib
import socket
import pytz
import uuid
from uuid import getnode as get_mac
from odoo.http import request
from netifaces import interfaces, ifaddresses, AF_INET
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
        readonly=True
    )
    client_factor_ref = fields.Char(
        string='Client Factor Reference',
        readonly=True
    )

    def _get_users_headers(self):
        return {
            "Gov-client-screens" : 'width='+ str(self.screen_width) +'&height='+ str(self.screen_height) +
                    '&scaling-factor='+ str(self.screen_scale) +'&colour-depth='+ str(self.screen_depth),
            "Gov-client-window-size" : 'width='+str(self.screen_width)+'&height='+ str(self.screen_height),
            "Gov-Client-Browser-Plugins" : str(self.browser_plugin),
            "Gov-Client-Browser-JS-User-Agent" : str(self.user_agent),
            "Gov-Client-Browser-Do-Not-Track" : str(self.browser_dnt).lower(),
        }

    def ip4_addresses(self):
        ip_list = []
        for interface in interfaces():
            for link in ifaddresses(interface).get(AF_INET, ()):
                ip_list.append(link['addr'])

        return ip_list

    def _get_vendor_headers(self, vendor_ip):
        return {
            "Gov-vendor-version":'Odoo%20SA=13.0&servercode=Python3.0',
            'Gov-vendor-license-ids': urllib.parse.urlencode({'Odoo':'13.0-20201006-community-edition'}),
            "Gov-vendor-public-ip": str(vendor_ip),
            "Gov-vendor-forwarded":'by='+str(vendor_ip)+'&for='+str(self.client_ip),
        }

    def _get_client_headers(self, company):
        now = str(datetime.now(pytz.timezone('UTC')).strftime('%Z%z'))
        multi_factor_now = str(datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%MZ'))
        if not self.client_factor_ref:
            self.write({'client_factor_ref': uuid.uuid4().hex[:13]})

        if not company.hmrc_username:
            raise exceptions.Warning('HMRC UserID Mandatory in Company')

        multi_factor = {
            'type': 'TOTP',
            'timestamp': str(multi_factor_now),
            'unique-reference': self.client_factor_ref,
        }
        return {
            "Gov-Client-Connection-Method": 'WEB_APP_VIA_SERVER',
            "Gov-Client-Public-IP": self.client_ip,
            "Gov-Client-Public-Port": str(request.httprequest.environ['REMOTE_PORT']),
            "Gov-Client-Device-Id": str(uuid.uuid1()),
            "Gov-Client-User-Ids": 'Odoo=opusvl'+ str(company.hmrc_username),
            "Gov-Client-Timezone": now[:-2] + ':' + now[-2:],
            "Gov-client-local-ips": ','.join(ip for ip in self.ip4_addresses()),
            "Gov-client-multi-factor": urllib.parse.urlencode(multi_factor),
        }

