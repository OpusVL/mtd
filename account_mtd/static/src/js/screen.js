openerp.account_mtd = function(instance) {
    var ClientIps = []

    instance.web.FormView.include({
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
        _onUpdateClientData: async function() {
            var self = this;
            // event.stopPropagation();
            var def;
            var d = $.Deferred();
            var clientinfo = window.clientInformation || window.navigator;
            var plugins = [];
            var dnt_res = false;
            var uuid = ''
            var user_model = new openerp.web.Model("res.users");
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
                    user_model.call(
                        "get_user_uuid4", 
                        [[self.dataset.context.uid]], 
                    {context:new openerp.web.CompoundContext()}).then(function(res) {
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
            var timezone_offset_min = new Date().getTimezoneOffset(),
                offset_hrs = parseInt(Math.abs(timezone_offset_min/60)),
                offset_min = Math.abs(timezone_offset_min%60),
                timezone_standard;

            if(offset_hrs < 10)
                offset_hrs = '0' + offset_hrs;

            if(offset_min < 10)
                offset_min = '0' + offset_min;

            // Add an opposite sign to the offset
            // If offset is 0, it means timezone is UTC
            if(timezone_offset_min < 0)
                timezone_standard = '+' + offset_hrs + ':' + offset_min;
            else if(timezone_offset_min > 0)
                timezone_standard = '-' + offset_hrs + ':' + offset_min;
            else if(timezone_offset_min == 0)
                timezone_standard = 'Z';
            timezone = 'UTC' + String(timezone_standard);

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
            user_model.call('write', [[self.dataset.context.uid], data_dict] ,{});
            def = d.promise();
        },
        load_record: function(data) {
            var self = this;
            this._super(data);
            if (this.model === 'mtd.hello_world' || this.model === 'mtd_vat.vat_endpoints') {
                this._onUpdateClientData();
            }
        },
    });

}
