# -*- coding: utf-8 -*-
{
    'name': "HelpDesk website access",
    'version': "0.1",
    'author': "Golubev",
    'category': "Tools",
    'complexity': 'easy',
    'support': "golubev@svami.in.ua",
    'summary': "A helpdesk / support ticket system (website support)",
    'description': """
A helpdesk / support ticket system
This module adds helpdesk tickets inside your account's page on website.
==================================================================================================
    """,
    'license':'LGPL-3',
    'data': [
        'views/helpdesk_templates.xml',
        'views/helpdesk_website_data.xml',
    ],
    'demo': [],
    'depends': ['helpdesk_lite','website_portal', "website_form"],
}
