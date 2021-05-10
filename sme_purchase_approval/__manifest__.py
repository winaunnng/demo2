# -*- coding: utf-8 -*-
{
    'name': "SMEi Purchase Approval",

    'summary': """
        Purchase Approval""",

    'description': """
        Purchase Approval
    """,

    'author': "SME Intellect Co. Ltd",
    'website': "https://www.smeintellect.com/",
    'category': 'Purchase Management',
    'version': '0.1',

    'depends': ['purchase'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_refuse_reason_views.xml',
        'views/purchase_view.xml',
        'data/mail_activity_data.xml',

    ],

}
