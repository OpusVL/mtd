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
                    var eval_context = c.get_eval_context();
                    var CaseCodeModel = new openerp.Model('account.tax.code');
                    var promise_from_do_action;
                    CaseCodeModel.call(
                        'move_line_domain_for_chart_of_taxes_row',
                        [],
                        {
                            tax_code_id: eval_context.active_id,
                            entry_state_filter: eval_context.state,
                            date_from: eval_context.date_from,
                            date_to: eval_context.date_to,
                            company_id: eval_context.company_id,
                            vat_filter: eval_context.vat,   // In funny tristate string format
                            with_children: true,
                        }
                    )
                    .then(function (returned_domain) {
                        action.domain = returned_domain;
                        // Making async call after this then() caused a race condition
                        promise_from_do_action = self.do_action(action);
                        return promise_from_do_action;  // Unsure if this is necessary along with above assignment
                    });
                }
                else
                {
                    promise_from_do_action = self.do_action(action);
                }
                return promise_from_do_action;
            });
        },
    });

})();
