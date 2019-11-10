from openerp import api, models
import openerp.addons.report.controllers.main as main
from openerp import http
from openerp.http import request
import unicodedata

class delivery_report(models.AbstractModel):
    _name = 'report.soupese_base.delivery_report'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('soupese_base.delivery_report')
        owner = self.env['res.partner'].search([('is_an_owner', '=', True)], limit=1)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'owner': owner,
        }
        return report_obj.render('soupese_base.delivery_report', docargs)


class report_controller(main.ReportController):
    
    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        isDO = False
        normalize_obj = unicodedata.normalize('NFKD', data).encode('ascii','ignore')

        if 'delivery_report' in normalize_obj:
            order_obj = http.request.env['stock.picking']
            isDO = True
        elif 'purchaseorder' in normalize_obj or 'purchasequotation' in normalize_obj:
            order_obj = http.request.env['purchase.order']
        else:
            response = super(report_controller, self).report_download(data, token)
            return response

        reportname = normalize_obj.split('/report/pdf/')[1].split('?')[0]
        reportname, docids = reportname.split('/')
        assert docids
        response = super(report_controller, self).report_download(data, token)
        object = order_obj.browse(int(docids))

        if isDO:
             filename = object.origin
        else:
             filename = object.name
       
        response.headers.set('Content-Disposition', 'attachment; filename=%s.pdf;' % filename)
        return response

