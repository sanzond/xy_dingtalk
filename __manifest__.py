# -*- coding: utf-8 -*-
{
    'name': "Dingtalk",

    'summary': """
        Dingtalk""",

    'description': """
        Api and methods for Dingtalk, which is used in Internal Enterprise Applications.
        Need python version >= 3.7
    """,

    'author': "funenc",
    'website': "https://www.funenc.com",

    'external_dependencies': {
        'python': ['aiohttp'],
    },

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    'assets': {
        'web.assets_backend': [
            'dingtalk/static/src/js/ding_qrcode_widget.js',
        ]
    },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/company.xml',
        'views/app.xml',
        'views/log.xml',
    ],
    # only loaded in demonstration mode
    'application': True,
}
