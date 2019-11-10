from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    @api.depends()
    def _get_purchase_id(self):
        res = False
        # purchase_obj = self.env['purchase.order.line'].search([('picking_id','=',self.id)],limit=1)
        for rec_id in self.move_lines:
            res = rec_id.purchase_line_id.order_id.id
            break
        self.purch_id = res

    # Related field to get fields from purchase.order inside of stock.picking
    purch_id = fields.Many2one('purchase.order', compute='_get_purchase_id', string="Purchase Order")

    def print_custom_do_report(self, cr, uid, ids, context=None):
        return self.pool['report'].get_action(cr, uid, ids, 'soupese_base.delivery_report')
