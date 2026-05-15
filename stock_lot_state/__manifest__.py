{
    "name": "Stock Lot State",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Add draft/reviewed states to stock lots",
    "author": "Comunitea",
    "website": "https://www.comunitea.com",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "product_expiry",
        "stock_lock_lot"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_lot_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
