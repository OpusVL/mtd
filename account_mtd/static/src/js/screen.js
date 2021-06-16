odoo.define('account_mtd.screen', function(require) {
    "use strict";

    var FormView = require('web.FormController');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var localStorage = require('web.local_storage');
    var _t = core._t;    

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
			var dnt_res = false;
			var uuid = ''
			
		    if (this.modelName === 'mtd.hello_world' || this.modelName === 'mtd_vat.vat_endpoints') {
	            var dnt = (typeof navigator.doNotTrack !== 'undefined')   ? navigator.doNotTrack
	                    : (typeof window.doNotTrack !== 'undefined')      ? window.doNotTrack
	                    : (typeof navigator.msDoNotTrack !== 'undefined') ? navigator.msDoNotTrack
	                    : null;
	            if (1 === parseInt(dnt) || 'yes' == dnt) {
	            	dnt_res = true
	            }
	            for(var i=0;i<clientinfo.plugins.length;i++){
	              	plugins.push(encodeURIComponent(clientinfo.plugins[i].name))
	            }
	            
	            if (localStorage.getItem('clientID') === null || localStorage.getItem('clientID') === '') {
	            	var result = $.Deferred();
    	            self._rpc({
    	                model: 'res.users',
    	                method: 'get_user_uuid4',
    	                args: [[record.context.uid]],
    	            }).then(function(res) {
    	            	uuid = res
    	            	result.resolve(res);
    	            	localStorage.setItem("clientID", uuid);
                    });
                    result.promise();
	            }
	            else {
	                uuid = localStorage.getItem('clientID')
	            }
	            
	            var data_dict = {
	            	'screen_width': screen.width,
	            	'screen_height': screen.height,
	            	'screen_depth': screen.colorDepth,
	            	'screen_scale': window.devicePixelRatio,
	            	'user_agent': clientinfo.userAgent,
	            	'browser_plugin': (plugins.length !== 0) ? plugins.join(',') : 'NoPlugins',
	            	'browser_dnt': dnt_res,
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
