# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "Soupese Base",
    'summary': "Provides Odoo customisations for Soupese",
    'description': """
Provides Odoo customisations for Soupese:\n\n

1. Chicken vendor and scale information\n
2. PDA models for history, API, and settings\n
3. Add custom Delivery Report in the Delivery Order\n
4. Customized Odoo web client interface/ debranding\n
5. Customized Purchase Order form and order lines\n
6. Customized Delivery form\n
    """,
    'author': "MyEvo",
    'category': 'backend',
    'version': '1.0',
    'depends': [
        'account',
        'base',
        'mail',
        'product',
        'purchase',
        'report',
        'sale',
        'stock',
        'web',
        'auth_signup',
        'portal',
    ],
    'data': [
        'reports/delivery_report.xml',
        'views/report_config.xml',
        'views/product_view.xml',
        'views/purchase_order_custom_view.xml',
        'views/report_purchase_order.xml',
        'views/pda_api_view.xml',
        'views/ch_vendor_info_view.xml',
        'views/res_partner_view.xml',
        'views/purchase_view.xml',
        'views/account_invoice_view.xml',
        'views/sale_view.xml',
        'views/base.xml',
        'views/discuss.xml',
        'wizard/change_pass.xml',
        'wizard/menu_profile.xml',
        'wizard/purchase_order_wizard.xml',
        'security/ir.model.access.csv',
        'security/soupese_base_security.xml',
        'data/header_field_view.xml',
    ],
    'qweb': [
        'static/src/xml/web_client_view.xml',
    ],
    'installable': True,
    'application': True
}
