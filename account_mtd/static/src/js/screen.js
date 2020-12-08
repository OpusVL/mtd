odoo.define('account_mtd.screen', function(require) {
    "use strict";

    var FormView = require('web.FormController');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;
    var clientIp = ''

    $.getJSON("https://api.ipify.org?format=json", function(data) { 
    	clientIp = data.ip
    }) 

	FormView.include({
		_onButtonClicked: function (event) {
			event.stopPropagation();
			var self = this;
			var def;
			var d = $.Deferred();
			var attrs = event.data.attrs;
			var record = event.data.record;
			var clientinfo = window.clientInformation || window.navigator;
			var plugins = [];
			var dnt_res = 'false';

		    if (event.data.attrs && 'id' in event.data.attrs && event.data.attrs.id === 'header_js_event') {
	            var dnt = (typeof navigator.doNotTrack !== 'undefined')   ? navigator.doNotTrack
	                    : (typeof window.doNotTrack !== 'undefined')      ? window.doNotTrack
	                    : (typeof navigator.msDoNotTrack !== 'undefined') ? navigator.msDoNotTrack
	                    : null;
	            if (1 === parseInt(dnt) || 'yes' == dnt) {
	            	dnt_res = 'true'
	            }
	            for(var i=0;i<clientinfo.plugins.length;i++){
	              	plugins.push(encodeURIComponent(clientinfo.plugins[i].name))
	            }

	            var data_dict = {
	            	'screen_width': screen.width,
	            	'screen_height': screen.height,
	            	'screen_depth': screen.colorDepth,
	            	'screen_scale': window.devicePixelRatio,
	            	'user_agent': clientinfo.userAgent,
	            	'browser_plugin': (plugins.length !== 0) ? plugins.join(',') : 'NoPlugins',
	            	'browser_dnt': dnt_res,
	            	'client_ip': clientIp,
	            }
	            self._rpc({
	                model: 'res.users',
	                method: 'write',
	                args: [[record.context.uid], data_dict],
	            }).then(function(res) {
                    return self.saveRecord(self.handle, {
                        stayInEdit: true,
                    }).then(function () {
                        // we need to reget the record to make sure we have changes made
                        // by the basic model, such as the new res_id, if the record is
                        // new.
                        var record = self.model.get(event.data.record.id);
                        return self._callButtonAction(attrs, record);
                	});
                });
	            def = d.promise();
		    } else {
		        this._super.apply(this, arguments);
		    }
		},
	});

});
