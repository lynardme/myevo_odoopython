from logging import getLogger

from openerp import fields, models

_logger = getLogger("purchase_order_custom")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    crates = fields.Integer(string="Number of Crates")
    crates_weight = fields.Float(string="Crates Weight (Kg)")
    crate_net = fields.Float("Est. Net Weight")
    weighing_date = fields.Datetime("Weighing Date")
    # total_crates = fields.Float('Total Crates', compute='_compute_crates',
    #                             store=True)

    # @api.depends('crates')
    # def _compute_crates(self):
    #     for line in self:
    #         print "lineself>>>", line
    #         line.update({'total_crates': line.total_crates + line.crates})


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
    pda_do_id = fields.Char('PDA DO id')
