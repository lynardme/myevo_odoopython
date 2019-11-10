from openerp import models, fields, api, _
from openerp import exceptions


class Partner(models.Model):
    _inherit = 'res.partner'   

    country_name = fields.Char(string='Country')
    state_name = fields.Char(string='State')

    supplier = fields.Boolean(
        string="Is a Vendor",
        help="""Check this box if this contact is a vendor.
        If it's not checked, purchase people will not see it when encoding a purchase order.""",
        default=True)

    @api.model
    def create(self, vals):
        is_an_owner = vals.get('is_an_owner')
        supplier = vals.get('supplier')
        if self._uid != 1: 
            if is_an_owner is False and supplier is False:
                raise exceptions.Warning(
                    _('Please select Purchase type ("Is a Vendor" or "Is an Owner") from "Sales & Purchases" tab.'))
            if is_an_owner is True and supplier is True:
                raise exceptions.Warning(
                    _("""You just allowed to select one Purchase type
                    ("Is a Vendor" or "Is an Owner") in "Sales & Purchases" tab."""))
        
        res = super(Partner, self).create(vals)
        
        if not res.is_an_owner and res.linked_to:
            owner_rec = self.env['res.partner'].search([('id', '=', res.linked_to.id)])
            if owner_rec:
                owner_rec.owner_ids = [(4, res.id)]
        return res

    @api.multi
    def unlink(self):
        if not self.is_an_owner and self.linked_to:
            owner_rec = self.env['res.partner'].search([('id', '=', self.linked_to.id)])
            if owner_rec and self.id in owner_rec.owner_ids.ids:
                owner_rec.owner_ids = [(2, self.id)]
        return super(Partner, self).unlink()

    @api.multi
    def write(self, vals):
        raise_err = 0
        record_supplier = False
        record_is_an_owner = False
        for rec in self:
            record_is_an_owner = rec.is_an_owner
            record_supplier = rec.supplier
        vals_is_an_owner = vals.get('is_an_owner')
        vals_supplier = vals.get('supplier')

        if vals_supplier is not None and vals_is_an_owner is not None:
            if vals_supplier is False and vals_is_an_owner is False:
                raise_err = 1
            elif vals_supplier is True and vals_is_an_owner is True:
                raise_err = 2
        elif vals_supplier is None and vals_is_an_owner is not None:
            if record_supplier is False and vals_is_an_owner is False:
                raise_err = 1
            elif record_supplier is True and vals_is_an_owner is True:
                raise_err = 2
        elif vals_supplier is None and vals_is_an_owner is None:
            if vals_supplier is False and record_is_an_owner is False:
                raise_err = 1
            elif vals_supplier is True and record_is_an_owner is True:
                raise_err = 2
        elif vals_supplier is None and vals_is_an_owner is None:
            if record_supplier is False and record_is_an_owner is False:
                raise_err = 1  
            elif record_supplier is False and record_is_an_owner is False:
                raise_err = 2            
        if self._uid != 1:  
            if raise_err == 1:
                raise exceptions.Warning(
                    _('Please select Purchase type ("Is a Vendor" or "Is an Owner") from "Sales & Purchases" tab.'))
            elif raise_err == 2:
                raise exceptions.Warning(
                    _("""You just allowed to select one Purchase type ("Is a Vendor" or "Is an Owner").
                    Please check the "Sales & Purchases" tab."""))
        
        if 'linked_to' in vals:
            if vals['linked_to']:
                owner_rec = self.env['res.partner'].search([('id', '=', vals.get('linked_to'))])
                if owner_rec and self.id not in owner_rec.owner_ids.ids:
                    owner_rec.owner_ids = [(4, self.id)]
            else:
                owner_recs = self.env['res.partner'].search([])
                for owner_rec in owner_recs:
                    if self.id in owner_rec.owner_ids.ids:
                        owner_rec.owner_ids = [(2, self.id)]


        return super(Partner, self).write(vals)


    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Payable", oldname="property_account_payable",
        domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=False)
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Receivable", oldname="property_account_receivable",
        domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=False)