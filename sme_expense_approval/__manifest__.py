# -*- coding: utf-8 -*-
{
    'name': "SMEi Expense Approval",

    'summary': """
        Expense Approval""",

    'description': """
        Expense Approval
    """,

    'author': "SME Intellect Co. Ltd",
    'website': "https://www.smeintellect.com/",
    'category': 'HR Expense',
    'version': '0.1',

    'depends': ['hr_expense'],

    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense_view.xml',
        'data/mail_activity_data.xml',

    ],

}
