from openerp import models, fields, api, _


class UserProfile(models.TransientModel):
    _name = "user.profile"

    name = fields.Char(string='Name')
    login = fields.Char(string='Email')

    @api.model
    def default_get(self, fields):
        res = super(UserProfile, self).default_get(fields)
        res['name'] = self.env.user.name
        res['login'] = self.env.user.login
        return res

    @api.multi
    def reset_password_email(self):
        user_obj = self.env.user
        return user_obj.sudo().action_reset_password()
