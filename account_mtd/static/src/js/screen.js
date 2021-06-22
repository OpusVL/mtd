odoo.define('account_mtd.screen', function(require) {
    "use strict";

    var FormView = require('web.FormController');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var localStorage = require('web.local_storage');
    var _t = core._t;   
    var ClientIps = []

	FormView.include({
		updateDisplay: function(newAddr){
		    var addrs = Object.create(null);
		    addrs["0.0.0.0"] = false;
    	    if (newAddr in addrs) return;
    	    else addrs[newAddr] = true;
    	    var displayAddrs = Object.keys(addrs).filter(function (k) { return addrs[k]; });
    	    ClientIps = displayAddrs.join(" or perhaps ") || "n/a";
    	    return ClientIps
		},
		grepSDP: function(sdp){
			var hosts = [];
			var self = this;
			sdp.split('\r\n').forEach(function (line) { 
			    if (~line.indexOf("a=candidate")) {    
			        var parts = line.split(' '),       
			            addr = parts[4],
			            type = parts[7];
			        if (type === 'host') return self.updateDisplay(addr);
			    } else if (~line.indexOf("c=")) { 
			        var parts = line.split(' '),
			            addr = parts[2];
			        return self.updateDisplay(addr);
			    }
			});
		},
		findIPsWithWebRTC: async function () {
			var self = this;
		    // *** Return a promise
		    return new Promise((resolve, reject) => {
		        var myPeerConnection =  window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
		        var pc = new myPeerConnection({iceServers: [{urls: "stun:stun.l.google.com:19302"}]}),
		        noop = function() {};
		        pc.createDataChannel("");
		        pc.createOffer(function(offerDesc) {
		            var getip = self.grepSDP(offerDesc.sdp);
		            pc.setLocalDescription(offerDesc, noop, noop);
		            if (getip) resolve(getip);
		        }, noop);
		        pc.onicecandidate = function(ice) {
		        	var get_dns = ''
		            if (ice.candidate) get_dns = self.grepSDP("a="+ice.candidate.candidate);
		        	resolve(get_dns)
		        };
		    });
		},
		_onButtonClicked: async function (event) {
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
			var timezone = ''
		    if (this.modelName === 'mtd.hello_world' || this.modelName === 'mtd_vat.vat_endpoints') {
		    	let getIp = await this.findIPsWithWebRTC();
	            // Client DoNotTrak
	            var dnt = (typeof navigator.doNotTrack !== 'undefined')   ? navigator.doNotTrack
	                    : (typeof window.doNotTrack !== 'undefined')      ? window.doNotTrack
	                    : (typeof navigator.msDoNotTrack !== 'undefined') ? navigator.msDoNotTrack
	                    : null;
	            if (1 === parseInt(dnt) || 'yes' == dnt) {
	            	dnt_res = true
	            }
	            // Client Plugins
	            for(var i=0;i<clientinfo.plugins.length;i++){
	              	plugins.push(encodeURIComponent(clientinfo.plugins[i].name))
	            }
	            // Client ID
	            if (localStorage.getItem('clientID') === null || localStorage.getItem('clientID') === '') {
	            	await new Promise((resolve, reject) => {
	    	            self._rpc({
	    	                model: 'res.users',
	    	                method: 'get_user_uuid4',
	    	                args: [[record.context.uid]],
	    	            }).then(function(res) {
	    	            	uuid = res
	    	            	resolve(res);
	    	            	localStorage.setItem("clientID", uuid);
	                    });
                    });
	            }
	            else {
	                uuid = localStorage.getItem('clientID')
	            }
	            //Client Timezone
	            timezone = 'UTC' + String(moment().utc().format("Z"));

	            var data_dict = {
	            	'screen_width': screen.width,
	            	'screen_height': screen.height,
	            	'screen_depth': screen.colorDepth,
	            	'screen_scale': window.devicePixelRatio,
	            	'user_agent': clientinfo.userAgent,
	            	'browser_plugin': (plugins.length !== 0) ? plugins.join(',') : 'NoPlugins',
	            	'browser_dnt': dnt_res,
	            	'client_ip_address': ClientIps,
	            	'client_device_id':uuid,
	            	'client_timezone': timezone
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


