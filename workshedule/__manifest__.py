# -*- coding: utf-8 -*-
{
    'name': "Work shedule lib",

    'summary': """
        Developers library to caclulate deadline from hours
        acording to work shedule and public holidays""",

    'description': """
    """,

    'author': "Golubev",
    'license': "LGPL-3",
    'website': "http://www.odoo-ukraine.com",

    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'application': False,
}