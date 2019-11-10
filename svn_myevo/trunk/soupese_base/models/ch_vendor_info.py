from openerp import models, fields, api, _
from openerp.exceptions import UserError


class VendorInfoScale(models.Model):
    _name = "measure.scale"

    name = fields.Char(string="Scale ID")
    installation = fields.Datetime(string='Installation')
    last_sampling = fields.Datetime(string='Last Sampling')
    scale = fields.Many2one('res.partner', 'Scale', domain=['|',('customer','=',True),('supplier','=',True)])
    nickname = fields.Char(string='Nickname')
    brand = fields.Char(string='Brand')
    scale_model = fields.Char(string='Scale Model')
    display_model = fields.Char(string='Display Model')
    display_fw_version = fields.Char(string='Display FW Version')
    Comm_id = fields.Char(string="Comm ID")
    last_sync = fields.Datetime(string="Last Sync")


class VendorInfo(models.Model):
    _inherit = "res.partner"

    scales = fields.One2many('measure.scale', 'scale', 'Scale')
    information_of_gst = fields.Char('Information of GST')
    last_delivery = fields.Datetime(string='Last Delivery')
    branch = fields.Char('Branch')
    is_an_owner = fields.Boolean(string='Is an Owner')
    is_an_owner_dummy = fields.Boolean(string='Is an Owner',
                                       readonly=True,
                                       compute='_get_is_an_owner')  # This field just use for manager and will be readonly
    owner_id = fields.Many2one('res.partner', 'owner id')
    owner_ids = fields.One2many('res.partner', 'owner_id', 'Farms')
    lorry_ids = fields.One2many('lorry.number', 'owner_id', 'Lorry')
    profile_min_crate = fields.Float(string='Profile Min. Crate')
    profile_max_crate = fields.Float(string='Profile Max. Crate')
    crate_cover_weight = fields.Integer('Crate Cover Weight', default=400)
    
    header_do_report = fields.Binary('Header DO Report')
    header_name = fields.Char(string='Header DO Report')

    # mobile
    mobile_header_do_report = fields.Binary('Mobile Header DO Report')
    mobile_header_name = fields.Char(string='Mobile Header DO Report')

    xaml_template = fields.Text(string='XAML Template')

    manager = fields.Char("Manager")
    linked_to = fields.Many2one('res.partner', string='Linked to', domain="[('is_an_owner','=',True)]")
    is_an_farm = fields.Boolean(string='Is a Farm')

    @api.multi
    def write(self, vals):
        if 'is_an_farm' in vals and vals.get('is_an_farm') == False:
            return super(VendorInfo, self).write(vals)
        elif 'supplier' in vals and vals.get('supplier') == False:
            if self.is_an_farm == True:
                raise UserError("Please select 'Is a Vendor' when 'Is a Farm' is selected.")
        return super(VendorInfo, self).write(vals)

    @api.onchange('is_an_farm')
    def onchange_farm(self):
        if self.is_an_farm:
            self.supplier = True

    @api.onchange('image')
    def onchange_logo(self):
        if self.image:
            pda_recs = self.env['pda.operation'].sudo().search([('full_sync', '!=', 1)])
            if pda_recs:
                pda_recs.write({'full_sync': 1})

    @api.onchange('xaml_template')
    def onchange_xaml_template(self):
        if self.xaml_template:
            pda_recs = self.env['pda.operation'].sudo().search([('full_sync', '!=', 1)])
            if pda_recs:
                pda_recs.write({'full_sync': 1})

    @api.onchange('header_do_report')
    def onchange_header_do_report(self):
        if self.header_do_report:
            pda_recs = self.env['pda.operation'].sudo().search([('full_sync', '!=', 1)])
            if pda_recs:
                pda_recs.write({'full_sync': 1})

    @api.onchange('mobile_header_do_report')
    def onchange_mobile_header_do_report(self):
        if self.mobile_header_do_report:
            pda_recs = self.env['pda.operation'].sudo().search([('full_sync', '!=', 1)])
            if pda_recs:
                pda_recs.write({'full_sync': 1})

    @api.onchange('header_name','mobile_header_name')
    def change_filename(self):
        """Function to change the name of file"""

        if not self.header_name:
            self.header_do_report = False
        if not self.mobile_header_name:
            self.mobile_header_do_report = False

    @api.one
    def _get_is_an_owner(self):
        self.is_an_owner_dummy = self.is_an_owner


class Users(models.Model):
    _inherit = "res.users"

    @api.model
    def create(self, vals):
        res = super(Users, self).create(vals)
        res.partner_id.write({'supplier': False})
        return res
