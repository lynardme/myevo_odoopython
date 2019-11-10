from openerp import models, fields, api, _


class UserProfileWizard(models.TransientModel):
    _name = "user.profile.wizard"

    def _get_user_id(self):
        user_obj = self.env.user
        return [
            (0, 0, {'user_id': user_obj.id, 'user_login': user_obj.login})
        ]

    user_ids = fields.One2many('user.profile.change.password', 'userwizard_id', string="Users", default=_get_user_id)

    @api.multi
    def change_password_custom(self):
        print "\n \n"
        print "change_password_custom"
        for user_id in self.user_ids:
            user_id.change_password_button_custom()
        print "\n \n"

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }


# return {'type': 'ir.actions.act_window_close'}
# 
#      wizard = self.browse(cr, uid, ids, context=context)[0]
#         need_reload = any(uid == user.user_id.id for user in wizard.user_ids)
# 
#         line_ids = [user.id for user in wizard.user_ids]
#         self.pool.get('change.password.user').change_password_button(cr, uid, line_ids, context=context)
# 
#         if need_reload:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'reload'
#             }
# 
#         return {'type': 'ir.actions.act_window_close'}

class UserProfilePasswordChange(models.TransientModel):
    _name = "user.profile.change.password"

    userwizard_id = fields.Many2one('user.profile.wizard', string="Wizard", required=True)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    user_login = fields.Char('User Login', readonly='True')
    new_password = fields.Char('New Password', default="")

    @api.multi
    def change_password_button_custom(self):
        user_obj = self.env.user
        user_obj.sudo().write({'password': self.new_password})

# def change_password_button(self, cr, uid, ids, context=None):
#         for line in self.browse(cr, uid, ids, context=context):
#             line.user_id.write({'password': line.new_passwd})
#         # don't keep temporary passwords in the database longer than necessary
#         self.write(cr, uid, ids, {'new_passwd': False}, context=context)
