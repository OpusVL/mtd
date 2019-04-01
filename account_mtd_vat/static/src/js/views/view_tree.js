(function() {

var instance = openerp;
    instance.web.TreeView.include({
        // Get details in listview
        activate: function(id) {
            var self = this;
            var local_context = {
                active_model: self.dataset.model,
                active_id: id,
                active_ids: [id]
            };
            var ctx = instance.web.pyeval.eval(
                'context', new instance.web.CompoundContext(
                    this.dataset.get_context(), local_context));
            return this.rpc('/web/treeview/action', {
                id: id,
                model: this.dataset.model,
                context: ctx
            }).then(function (actions) {
                if (!actions.length) { return; }
                var action = actions[0][2];
                var c = new instance.web.CompoundContext(local_context).set_eval_context(ctx);
                if (action.context) {
                    c.add(action.context);
                }
                action.context = c;
                if (action.src_model == 'account.tax.code' && action.res_model == 'account.move.line') {
                // Ideally, we shouldn't fudge the domain like this, but instead eval it and convert it to a list of tuples instead of a string
                // Then we can properly add the additional domain criteria in, instead of just stitching it onto the end of the string
                // We assume the existing domain is always going to be the same like this.
                    if ((typeof c.__eval_context.vat !== 'Undefined') && (c.__eval_context.vat != "")){
                        var vat = c.__eval_context.vat
                        action.domain = ("[('tax_code_id', 'child_of', active_id), ('state', '!=', 'draft'), " +
                        "('period_id', 'in', [" + c.__eval_context.period_id + "]), ('vat', '=', " + c.__eval_context.vat + ")]")
                        //, ('vat', '=', vat)]
                    } else {
                        action.domain = ("[('tax_code_id', 'child_of', active_id), ('state', '!=', 'draft'), " +
                        "('period_id', 'in', [" + c.__eval_context.period_id + "])]")
                    }
                }
                return self.do_action(action);
            });
        },
    });

})();
