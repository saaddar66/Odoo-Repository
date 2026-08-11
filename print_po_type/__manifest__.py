{
    'name': 'Print PO Type',
    'version': '18.0',
    'category': 'Purchase',
    'summary': 'Custom Purchase Order Reports',
    'description': """
        Adds custom Purchase Order reports like "Import" type.
    """,
    'depends': ['purchase'],
    'data': [
        'report/purchase_order_reports.xml',
        'report/purchase_order_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}