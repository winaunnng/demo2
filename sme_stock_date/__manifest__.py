# -*- coding: utf-8 -*-
{
    'name': "SMEi Inventory Date Custom",

    'summary': """
       Inventory Backdate Operations Control""",

    'description': """
     The following operations are currently supported with backdate including accounting entries
      1.Stock Transfer
      2.Inventory Adjustment
      4.Stock Scrapping
    """,

    'author': "SME Intellect Co. Ltd",
    'website': "https://www.smeintellect.com/",
    'category': 'Inventory Management',
    'version': '0.1',

    'depends': ['stock'],

    'data': [

        'views/stock_view.xml',

    ],

}
