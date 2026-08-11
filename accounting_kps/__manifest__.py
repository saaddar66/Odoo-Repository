{
    'name': 'Accounting KPS',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Vendor Bill Approval Workflow',
    'description': """
        Adds an approval workflow to manual vendor bills.
        Manual vendor bills require approval before they can be posted.
    """,
    'author': 'Antigravity',
    'depends': ['account', 'purchase'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
