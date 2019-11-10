from openerp import models, fields, api, _
import hashlib
from logging import getLogger

_logger = getLogger("API_PDA_receiver")


class PDAAPI(models.Model):
    _name = 'pda.api'

    db_name = fields.Char(string="Database Name")
    url_path = fields.Char(string="URL Path")
    user_name = fields.Char(string="Username")
    admin_pass = fields.Char(string="User Password", size=64, invisible=1, copy=False)
    token = fields.Char(string="Token")

    database_name = fields.Char(string="Database", readonly=True)
    url_name = fields.Char(string="URL", readonly=True)
    username = fields.Char(string="Username", readonly=True)
    password = fields.Char(string="Password", readonly=True, invisible=0, size=64)

    @api.onchange('db_name')  # if these fields are changed, call method
    def check_change_db(self):
        self.database_name = self.db_name

    @api.onchange('url_path')  # if these fields are changed, call method
    def check_change_ulr(self):
        self.url_name = self.url_path

    @api.onchange('user_name')  # if these fields are changed, call method
    def check_change_user(self):
        user = self.env['res.users'].search([('login', '=', self.user_name)])
        self.username = user.id

    @api.onchange('admin_pass')  # if these fields are changed, call method
    def check_change_pass(self):
        self.password = self.admin_pass

    @api.model
    def default_get(self, vals):
        res = super(PDAAPI, self).default_get(vals)
        pda_api_obj = self.env['pda.api'].search([])

        if len(pda_api_obj) == 0:
            val = dict()
            val['user_name'] = False
            val['db_name'] = False
            val['url_path'] = False
            val['admin_pass'] = False
            self.env['pda.api'].create(val)
        else:
            for rec in pda_api_obj:
                res.update({
                    'user_name': rec.user_name,
                    'db_name': rec.db_name,
                    'url_path': rec.url_path,
                    'admin_pass': rec.admin_pass,
                })
                break
        return res

    @api.multi
    def execute(self):
        pda_setting = self.env['pda.api'].search([])
        values = {}
        if pda_setting[0]:
            values['user_name'] = self.user_name or False
            values['db_name'] = self.db_name or False
            values['url_path'] = self.url_path or False
            values['admin_pass'] = self.admin_pass or False
            values['database_name'] = self.database_name or False
            pda_setting[0].write(values)
        return {
            'type': 'ir.actions.act_window',
            'name': _('PDA Settings'),
            'res_model': 'pda.api',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'inline'}

    @api.multi
    def cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('PDA Settings'),
            'res_model': 'pda.api',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'inline'}

    @api.model
    def create_purchase_order(self, po_body):
        # prepare var partner_id
        if 'partner_id' in po_body:
            partner = self.env['res.partner'].search([('name', '=', po_body['partner_id'])])
            partner = partner.id
        else:
            return 'No exist partner_id'
        # prepare var date
        if 'date' in po_body:
            date = po_body['date']
        else:
            return 'No exist date'
        # prepare var farm_id
        if 'farm_id' in po_body:
            print po_body['farm_id']
            farm = self.env['res.partner'].search([('name', '=', po_body['farm_id'])])
            farm = farm.id
        else:
            return 'No exist farm_id'
        # prepare var scale_id
        if 'scale_id' in po_body:
            scale = self.env['measure.scale'].search([('name', '=', po_body['scale_id'])])
            scale = scale.id
        # prepare var pod_id
        if 'pda_id' in po_body:
            pda = self.env['pda.operation'].search([('name', '=', po_body['pda_id'])])
            pda = pda.id
        else:
            return 'No exist farm_id'
        # prepare var off_feeding
        if 'off_feeding' in po_body:
            off_feeding = po_body['off_feeding']
        else:
            return 'No exist off_feeding'
        # prepare var water_fogging
        if 'water_fogging' in po_body:
            water_fogging = po_body['water_fogging']
        else:
            return 'No exist off_feeding'
        # prepare var lory_number
        if 'lory_number' in po_body:
            lory_number = po_body['lory_number']
        else:
            return 'No exist lory_number'
        # total_gross_weight
        if 'total_gross_weight' in po_body:
            total_gross_weight = po_body['total_gross_weight']
        else:
            return 'No exist total_gross_weight'
        po_dict = {'partner_id': partner,
                   'date_order': date,
                   'farm_id': farm,
                   'scale_id': scale,
                   'pda_id': pda,
                   'currency_id': self.env.user.company_id.currency_id.id,
                   'off_feeding': off_feeding,
                   'water_fogging': water_fogging,
                   'lory_number': lory_number,
                   'total_gw': float(total_gross_weight),
                   }
        po_id = self.env['purchase.order'].create(po_dict)
        return po_id.id

    @api.model
    def create_orderline(self, line_bodies):
        for line_body in line_bodies:
            # prepare var partner_id
            if 'product_id' in line_body:
                product = self.env['product.template'].search([('name', '=', line_body['product_id'])])
                description = product.name
                product = product.id
            else:
                return 'No exist product'
            # prepare var date
            if 'crates' in line_body:
                crates = line_body['crates']
            else:
                return 'No exist crates'
            # prepare var farm_id
            if 'crates_weight' in line_body:
                crates_weight = line_body['crates_weight']
            else:
                return 'No exist crates_weight'
            # prepare var scale_id
            if 'product_qty' in line_body:
                qty = int(line_body['product_qty'])
            else:
                qty = 0
            if 'male' in line_body:
                male = int(line_body['male'])
            else:
                male = 0
            if 'female' in line_body:
                female = int(line_body['female'])
            else:
                female = 0
            if 'apollo' in line_body:
                apollo = int(line_body['apollo'])
            else:
                apollo = 0
            if 'buyer' in line_body:
                buyer = line_body['buyer']
            else:
                return 'No exist Buyer'
            if 'order_id' in line_body:
                order = line_body['order_id']
            else:
                return 'No exist Order'
            # Temporary logging
            _logger.error("***PO LINES PARAMS***: %s" % str(line_body))
            line_dict = {
                'order_id': order,
                'product_id': product,
                'name': description,
                'crates': crates,
                'crates_weight': crates_weight,
                'crate_net': line_body.get('crate_net'),
                'product_qty': male + female + apollo,
                'male': male,
                'female': female,
                'apollo': apollo,
                'product_uom': 1,
                'buyer': buyer,
                'weighing_date': line_body.get('weighing_date')}
            po_line_id = self.env['purchase.order.line'].create(line_dict)
        return po_line_id.id

    @api.model
    def action_confirm_po(self, order_id):
        purchase_obj = self.env['purchase.order'].search([('state', '=', 'draft'), ('id', '=', order_id)])
        for purchase in purchase_obj:
            """
            FIXED BUG: Fault: <Fault warning -- You must set a Vendor Location for this partner
            Sometimes the Vendor Location become empty causing the creation PO fails.

            SOLUTION: Set back the default Vendor Location
            """
            if purchase.partner_id.property_stock_supplier.id == False:
                res_partner_obj = self.env['res.partner'].search([('id', '=', purchase.partner_id.id)])
                for farm in res_partner_obj:
                    stock_location_obj = self.env['stock.location'].search([('name', '=ilike', 'Vendors'),
                        ('usage','=ilike','supplier')])
                    farm.write({'property_stock_supplier': stock_location_obj.id})
                    _logger.warning("Vendor Location was empty for res_partner-id:%s,name:%s" % 
                        (str(purchase.partner_id.id), purchase.partner_id.name))
            purchase.button_confirm()
        return True

    @api.model
    def action_confirm_so(self, order_id):
        sale_obj = self.env['sale.order'].search([('state', '=', 'draft'), ('id', '=', order_id)])
        for sale in sale_obj:
            sale.action_confirm()
        return True

    @api.model
    def get_farm(self):
        farms = []
        for i in self.env['res.partner'].search([('supplier', '=', True), ('customer', '=', False)]):
            farm = dict()
            farm['id'] = i.id
            farm['name'] = i.name
            farms.append(farm)
        return farms

    @api.model
    def get_scale(self):
        scales = []
        for i in self.env['measure.scale'].search([]):
            scale = dict()
            scale['id'] = i.id
            scale['name'] = i.name
            scales.append(scale)
        return scales

    @api.model
    def get_company(self):
        companies = []
        for i in self.env['res.company'].search([]):
            company = dict()
            company['name'] = i.name
            company['street'] = i.street
            company['street2'] = i.street2
            company['city'] = i.city
            company['state_id'] = i.state_id.name
            company['zip'] = i.zip
            company['country_id'] = i.country_id.name
            company['tax_id'] = i.vat
            companies.append(company)
        return companies


class PDAHistory(models.Model):
    _name = 'pda.history'
    _order = 'id desc'

    name = fields.Many2one('pda.operation', 'PDA Model')
    owner_id = fields.Many2one('res.company', 'Owner')
    last_position_long = fields.Char('Last Position Long')
    last_position_latt = fields.Char('Last Position Latt')
    last_sync_with_erp = fields.Datetime('Last Sync with ERP')
    access_date = fields.Datetime('Access Date')
    info = fields.Selection(
        [('order_create', "order_create"), ('getmasterupdate', "getmasterupdate")],
        'Information')
    data = fields.Char('Raw Data')
    url_loc = fields.Char('Google map link', compute='_get_google_map')

    @api.multi
    def _get_google_map(self):
        for rec in self:
            rec.url_loc = "http://www.google.com/maps/place/%s,%s" % (rec.last_position_latt, rec.last_position_long)

class PDAOperation(models.Model):
    _name = 'pda.operation'
    _rec_name = "pda_id"

    name = fields.Char(string="Model")
    lorry_id = fields.Many2one('lorry.number', string="PDA ID")
    pda_id = fields.Char(string="ID")
    installation = fields.Datetime(string="Installation")
    lastest_sync = fields.Char(string="Last Sync", readonly=True)
    pda_history_ids = fields.One2many('pda.history', 'name', string="PDA History")
    app_version = fields.Char(string='App Version')
    full_sync = fields.Integer(string='Full Sync', default=1)

class User(models.Model):
    _inherit = 'res.users'

    token = fields.Char('API Key')

    @api.multi
    def get_token(self):
        user = 'this is token encrption' + str(self.login)
        tok = hashlib.md5(user).hexdigest()
        self.write({'token': tok})
        return True
