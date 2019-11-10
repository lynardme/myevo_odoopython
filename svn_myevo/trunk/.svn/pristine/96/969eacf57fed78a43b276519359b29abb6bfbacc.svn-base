from openerp import models, fields, api, _
from datetime import datetime
import hashlib
from logging import getLogger

_logger = getLogger("purchase_order_custom")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('partner_id', 'farm_house_number')
    def _concat_farm_house(self):
        for rec in self:
            rec.farm_house_concat = rec.partner_id.name + ' / ' + rec.farm_house_number if rec.partner_id.name and rec.farm_house_number else False

    # Print DO report from SO form
    @api.multi
    def print_do_report(self):
        if self.name:
            do_obj = self.env['stock.picking'].search([('origin', '=', self.name)])
            for do in do_obj:
                return do.print_custom_do_report()

                # Set default currency to usd (Try to ignore currency field)

    @api.one
    @api.depends('order_id.currency_id')
    def _set_defult_currency(self):
        current_user = self.env.user
        curr_id = self.env['res.currency'].search([('name', '=', 'USD')])
        for cur in curr_id:
            currency_id = cur.id

        # Try to ignore location_id field
        stock_id = self.env['stock.move']
        stock_id.location_id = self.partner_id.property_stock_supplier.id

    @api.multi
    def write(self,vals):
        # recalculate
        is_order_line = True if 'order_line' in vals else False
        flags = dict.fromkeys(["crates", "crates_weight", "crate_net"], False)
        if is_order_line:
            for line in vals['order_line']:
                if line[0] == 1:
                    if 'crates' in line[2]:
                        flags['crates'] = True
                    if 'crate_net' in line[2]:
                        flags['crate_net'] = True
                    if 'crates_weight' in line[2]:
                        flags['crates_weight'] = True
        res = super(PurchaseOrder, self).write(vals)

        if is_order_line:
            res_order_line = self.env['purchase.order.line'].search([('order_id', '=', self.id)])

            total_crates, total_gw, total_nw, total_cw = 0, 0, 0, 0

            for line in res_order_line:
                if flags['crates']:
                    total_crates += line.crates
                if flags['crates_weight']:
                    total_gw += line.crates_weight
                if flags['crate_net']:
                    total_nw += line.crate_net

            newvals = {}
            if flags['crates']:
                total_cw = self.avg_cr_w * total_crates
                newvals.update({'total_crates': total_crates, 'total_cw': total_cw})
            if flags['crates_weight']:
                newvals.update({'total_gw': total_gw})    
            if flags['crate_net']:
                newvals.update({'total_nw': total_nw})

            res = super(PurchaseOrder, self).write(newvals)

        return res

    # Remove mandatory and hide them in view
    currency_id = fields.Many2one('res.currency', 'Currency', required=False, default=_set_defult_currency)

    # remove mandatory
    partner_id = fields.Many2one('res.partner', required=False)

    # Store Confirmation Date
    # confirm_date = fields.Datetime(string="Date", readonly=False)
    confirm_date = fields.Char(string="Date", readonly=False)

    # Store Signature Of Customer And Farmer In Charge
    customer_signature = fields.Binary(string="Customer Signature",
                                       store=True)
    farmer_signature = fields.Binary(string="Farmer Signature",
                                     store=True)

    # Additional Form Fields
    # 	farm_id = fields.Many2one('res.partner',string="Farm") use partner_id instead of this field
    owners_id = fields.Many2one('res.partner', string="Owner",
                                compute='_get_owner_id')
    scale_id = fields.Many2one('measure.scale', string="Scale ID", readonly=False)
    pda_id = fields.Many2one('pda.operation', string="PDA ID", readonly=False)
    # 	pda_id = fields.Char(string="PDA ID", readonly=True)
    off_feeding = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                   string="Off Feeding", readonly=False)
    water_fogging = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                     string="Water Fogging", readonly=False)
    # 	lory_number = fields.Char(string="Truck/Lorry Number", readonly=True)
    lory_number = fields.Many2one('lorry.number', string="Truck/Lorry Number", readonly=False)

    # Additional Footer Fields
    # crates_weight = fields.Float(string="Total Gross Weight (kg)", readonly=False)

    total_gw = fields.Float(string="Total Gross Weight (kg)", readonly=False)
    avg_cr_w = fields.Float(string="Av. Crates Weight (kg)", readonly=False)  # compute='_get_avg_cr_w',
    total_cw = fields.Float(string="Total Crates Weight (kg)", readonly=False)  # compute='_get_total_cw',
    avg_b_w = fields.Float(string="Av. Bird Weight (kg)", readonly=False)  # compute='_get_avg_b_w',
    total_nw = fields.Float(string="Total DOs Net Weight (kg)", readonly=False)  # compute='_get_total_nw',

    total_male = fields.Integer(string="Total Male", readonly=False)  # compute='_get_total_ml',
    total_female = fields.Integer(string="Total Female", readonly=False)  # compute='_get_total_fe',
    total_apollo = fields.Integer(string="Total Apollo", readonly=False)  # compute='_get_total_ap',
    total_crates = fields.Integer(string="Total Crates", readonly=False)  # compute='_get_total_cr',

    totalcover = fields.Float(string="Total Added Covers")
    single_cover_weight = fields.Float(string="Cover Weight (kg)")

    # additional field

    pda_do_id = fields.Char('PDA DO id')
    start_loading_time = fields.Char('Start Loading Time')
    end_loading_time = fields.Char('End Loading Time')
    other_comment = fields.Text(string="Other Comments")

    # added 20171221
    product = fields.Char(string='Product')
    breed = fields.Char(string='Breed')
    age = fields.Char(string='Age')
    farm_house_number = fields.Char(string="House Number")
    total_nb_birds = fields.Char(string="Total Birds")
    batch_id = fields.Char(string="Batch ID")
    birdcrate_mix = fields.Char(string="Mix")
    birdcrate_mix_crates = fields.Float()
    birdcrate_mix_total = fields.Float(string="Total Mix")
    birdcrate_mix_avg = fields.Float()
    birdcrate_c = fields.Char(string="C")
    birdcrate_c_crates = fields.Float()
    birdcrate_c_total = fields.Float(string="Total Others")
    birdcrate_c_avg = fields.Float()
    birdcrate_b = fields.Char(string="B")
    birdcrate_b_crates = fields.Float()
    birdcrate_b_total = fields.Float(string="Total SX")
    birdcrate_b_avg = fields.Float()
    birdcrate_male = fields.Char(string="Male")
    birdcrate_male_crates = fields.Float()
    birdcrate_male_total = fields.Float()
    birdcrate_male_avg = fields.Float()
    birdcrate_female = fields.Char(string="Female")
    birdcrate_female_crates = fields.Float()
    birdcrate_female_total = fields.Float()
    birdcrate_female_avg = fields.Float()

    farm_house_concat = fields.Char(string='Farm / House#', compute='_concat_farm_house', store=True)


    # replace field state -- Togar
    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Reviewed'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')

    catching_bill = fields.Char(string="Catching Bill")

    @api.multi
    def _get_owner_id(self):
        res_partner_obj = self.env['res.partner'].search([('is_an_owner', '=', True)], limit=1)
        for res_partner in res_partner_obj:
            for rec in self:
                rec.owners_id = res_partner.id


# @api.multi
# 	def action_confirm(self):
# 		# Store Confirm Date Here With Current Date
# 		# if repeat all parts of exist function, no need to use super
# 		# ============================================================
# 		today = datetime.now()
# 		today = datetime.strftime(today, '%Y-%m-%d %H:%M:%S')
# 		# if use api depend or onchange, no need use write		
# 		self.write({'confirm_date': today})
# 		# append new codes to the old function with super method
# 		return super(purchase_order, self).action_confirm()
# 		# ============================================================

# 	@api.one
# 	def _get_avg_cr_w(self):
# 		result = 0.00
# 		for line in self.order_line:
# 			result += line.crates
# 		if result != 0:
# 			self.avg_cr_w = round((self.total_cw / self.total_crates), 2)
# 		else:
# 			self.avg_cr_w = 0 
# 		
# 	@api.one
# 	def _get_total_cw(self):
# 		result = 0.00
# 		for line in self.order_line:
# 			result += (line.crates_weight * line.crates)
# 		self.total_cw = result
# 
# 	@api.one
# 	def _get_avg_b_w(self):
# 		total_units = (self.total_male + self.total_female + self.total_apollo)
# 		if total_units != 0:
# 			self.avg_b_w = round((self.total_nw / total_units), 2)
# 		else:
# 			self.avg_b_w = 0
# 
# 	@api.one
# 	def _get_total_nw(self):
# 		self.total_nw = (self.total_gw - self.total_cw)
# 
# 	@api.one
# 	def _get_total_ml(self):
# 		result = 0.00
# 		for line in self.order_line:
# 			result += line.male
# 		self.total_male = result
# 		
# 	@api.one
# 	def _get_total_fe(self):
# 		result = 0.00
# 		for line in self.order_line:
# 			result += line.female
# 		self.total_female = result
# 		
# 	@api.one
# 	def _get_total_ap(self):
# 		result = 0.00
# 		for line in self.order_line:
# 			result += line.apollo
# 		self.total_apollo = result
# 		
# 	@api.one
# 	def _get_total_cr(self):
# 		result = 0.00
# 		for line in self.order_line:
# 			result += line.crates
# 		self.total_crates = result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _order = "weighing_date asc"

    # Set default product (Chicken) in purchase order line
    def _set_default_product(self):
        product_obj = self.env['product.product'].search([('name', '=', 'Chicken')])
        product_id = False
        if not product_obj:
            prod = self.env['product.product'].create({'name': "Chicken"})
            product_id = prod.id
        else:
            for product in product_obj:
                product_id = product.id
        return product_id

    # Remove required fields on purchase order line
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 domain=[('purchase_ok', '=', True)],
                                 required=False)
    price_unit = fields.Float(string='Unit Price',
                              required=False, default=0.00)
    date_planned = fields.Datetime(string='Scheduled Date',
                                   required=False, select=True,
                                   default=datetime.today())

    # 	order_line = fields.One2many('purchase.order.line', 'order_id', string='Order Lines', copy=True)
    # 	order_id = fields.Many2one('purchase.order', string='Order Reference', select=True, required=True, ondelete='cascade')

    # @api.one
    # def _get_total_lw(self):
    # 	total_units = (self.male + self.female + self.apollo)
    # 	self.total_lw = round((self.order_id.avg_b_w * total_units), 2)

    # Additional Sale Order Line Fields
    crates = fields.Integer(string="Number of Crates")
    crates_weight = fields.Float(string="Crates Weight (Kg)")
    crate_net = fields.Float("Est. Net Weight")
    weighing_date = fields.Datetime("Weighing Date")
    male = fields.Integer(string="Male")
    female = fields.Integer(string="Female")
    apollo = fields.Integer(string="Apollo",
                            digits=(20, 2))  # limited to 20 char
    # total_lw = fields.Float(compute='_get_total_lw',
    # 						string="Total Line Weight")
    buyer = fields.Char(string="Buyer", size=20)
    buyer_id = fields.Integer(string="Buyer id")

    nb_added_cover = fields.Char(string="Added Cover")

    @api.multi
    def write(self, vals):
        if 'date_order' in vals and not vals.get('date_order'):
            for rec in self:
                rec.date_order = rec.order_id.date_order
        return super(PurchaseOrderLine, self).write(vals)

    @api.model
    def create(self, vals):
        _logger.error("***CREATING PO LINE WITH VALUES: %s" % str(vals))
        rec = super(PurchaseOrderLine, self).create(vals)
        if not rec.date_order:
            rec.date_order = rec.order_id.date_order
        return rec


class LorryNumber(models.Model):
    _name = 'lorry.number'

    name = fields.Char(string="Plate Number")
    pda_ids = fields.One2many('pda.operation', 'lorry_id', string='PDA')
    owner_id = fields.Many2one('res.partner', 'Owner')
