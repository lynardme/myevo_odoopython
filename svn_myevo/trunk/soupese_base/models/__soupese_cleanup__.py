from openerp import models, api


# noinspection SqlNoDataSourceInspection
class CleanUp(models.TransientModel):
    _name = 'soupese_base.clean_up'

    # noinspection SqlDialectInspection
    @api.model
    def _clean_database(self):
        """ Cleans the database before fully installing the module
        by uninstalling old Soupese modules and remapping data
        """
        # noinspection PyUnresolvedReferences
        env = self.env
        cr = env.cr
        modules_to_resolve = [
            'ch_vendor_info',
            'API_PDA_receiver',
            'delivery_report_custom',
            'myevo_base',
            'myevo_nobutton_sending_email',
            'myevo_web',
            'purchase_order_custom']

        # Rename model module ch_vendor_info
        cr.execute("""UPDATE ir_model_data SET module = 'soupese_base' WHERE module = 'ch_vendor_info'""")
        # Delete module soupese_base models that exists in old models
        cr.execute("""DELETE FROM ir_model_data WHERE module = 'soupese_base' AND name = 'model_res_users'""")
        # Rename
        cr.execute("""UPDATE ir_model_data SET module = 'soupese_base' WHERE module = 'API_PDA_receiver'""")

        # Rename module
        cr.execute("""UPDATE ir_model_data SET module = 'soupese_base' WHERE module = 'delivery_report_custom'""")
        cr.execute("""UPDATE ir_model_data SET module = 'soupese_base' WHERE module = 'myevo_base'""")
        cr.execute(
            """UPDATE ir_model_data SET module = 'soupese_base' WHERE module = 'myevo_nobutton_sending_email'""")
        cr.execute("""UPDATE ir_model_data SET module = 'soupese_base' WHERE module = 'myevo_web'""")

        # Delete module soupese_base models that exists in old models
        cr.execute("""DELETE FROM ir_model_data WHERE module = 'soupese_base' AND name = 'model_measure_scale'""")
        cr.execute("""DELETE FROM ir_model_data WHERE module = 'soupese_base' AND name = 'model_pda_operation'""")
        cr.execute("""DELETE FROM ir_model_data WHERE module = 'soupese_base' AND name = 'model_res_partner'""")

        # Rename module
        cr.execute("""UPDATE ir_model_data SET module = 'soupese_base' WHERE module = 'purchase_order_custom'""")

        # Rename module_ in base
        for x in modules_to_resolve:
            cr.execute("""
              DELETE FROM ir_model_data
                WHERE name = 'module_%s' AND module = 'base' AND model = 'ir.module.module'""", (x,))

            # Uninstall modules
            cr.execute("""UPDATE ir_module_module SET state = 'uninstalled' WHERE name = '%s'""", (x,))

        # Remove vendor.information.scale table
        cr.execute("DROP TABLE vendor_information_scale")

        # Commit finally
        cr.commit()
