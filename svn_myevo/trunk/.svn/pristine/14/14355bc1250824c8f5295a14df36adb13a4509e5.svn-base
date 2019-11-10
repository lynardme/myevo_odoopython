from openerp import models, api, fields, _
from openerp.exceptions import Warning

class Discuss(models.Model):
    _inherit = 'mail.channel'

    allow_user_unsubscribe = fields.Boolean()
    partner_name = fields.Char(compute = "_compute_partner_name")

    @api.multi
    def _compute_partner_name(self):
        for record in self:
            record.partner_name = self.env.user.partner_id.name

    @api.multi
    def action_unfollow(self):
        channel_info = self.channel_info('unsubscribe')[0] 
        if str(self.partner_name) != "Administrator" and channel_info["public"] == "public" and self.allow_user_unsubscribe is False:
            raise Warning(_('Non-admin user cannot unsubscribe channel'))
        channel = super(Discuss, self).action_unfollow()
        return channel