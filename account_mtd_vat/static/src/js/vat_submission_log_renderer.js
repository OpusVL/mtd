openerp.account_mtd_vat = function (require) {
"use strict";

var rpc = require('web.rpc');
var validate_md5 = rpc.query({
    model: 'mtd_vat.vat_submission_logs',
    method: 'validate_md5_onload',
    args:[[]]
    }).then(function(ret){
        validate_md5 = ret
    });

};