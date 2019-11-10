odoo.define('soupese_base.PivotView', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;

    var PivotView = require('web.PivotView').include({

        /**Override render_buttons function of PivotView to sort the fields in alphabetical order **/
        render_buttons: function ($node) {
            if ($node) {
                var self = this;

                var x_measures = _.pairs(_.omit(this.measures, '__count__'));
                var sorted_x_measures = _.sortBy(x_measures, function (item) {
                    return item[1]['string'];
                });
                var context = {measures: sorted_x_measures};
                this.$buttons = $(QWeb.render('PivotView.buttons', context));
                this.$buttons.click(this.on_button_click.bind(this));
                this.active_measures.forEach(function (measure) {
                    self.$buttons.find('li[data-field="' + measure + '"]').addClass('selected');
                });
                this.$buttons.find('button').tooltip();

                this.$buttons.appendTo($node);
            }
        },

        /** Override prepare_fields function of PivotView **/
        prepare_fields: function (fields) {
            var self = this,
                groupable_types = ['many2one', 'char', 'boolean',
                    'selection', 'date', 'datetime'];
            if (self.model.name == 'purchase.order') {
                delete fields.amount_total;
                delete fields.amount_untaxed;
                delete fields.amount_tax;
            }
            this.fields = fields;
            _.each(fields, function (field, name) {
                if ((name !== 'id') && (field.store === true)) {
                    if (field.type === 'integer' || field.type === 'float' || field.type === 'monetary') {
                        self.measures[name] = field;
                    }
                    if (_.contains(groupable_types, field.type)) {
                        self.groupable_fields[name] = field;
                    }
                }
            });
            this.measures.__count__ = {string: _t("Count"), type: "integer"};
        },
    });

});