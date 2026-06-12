# Pharmadus Base Module - Complete Description

## Purpose
Base module for company-specific customizations in Pharmadus Botanicals Odoo instance (v18.0).

## What Does It Do?

### Core Functionality
- **Hierarchical Product Catalog**: Manages product lines → sublines relationships with company constraints
- **Stock Management**: Extends stock lots with packaging information and batch count tracking  
- **Sale Transfers**: Custom quotation system for distributor orders
- **Purchase Organization**: Separate purchase catalog by function (components, logistics, merchandise)

### Extended Features
- Product specifications per template (quantity tiers, packaging hierarchy)
- Lot state management (draft/reviewed states) for quality control
- Foretated product reporting with partner information enrichment
- Stock valuation layer extensions showing full spec details

## Module Dependencies Summary

### Required (Hard)
```yaml
"depends": [
    "base",      # Always present
    "mail",      # Notifications (templates, composer)
    "sale",      # Sales management
    "purchase",  # Purchase requisitions & orders
    "stock",     # Inventory operations
    "account",   # Accounting/invoicing
    "stock_account"  # Valuation layers
]
```

### Optional Soft Dependencies  
- `stock_picking_auto_create_lot` - Automatic lot creation on receiving
- `product_expiry` - Lot expiration tracking (if applicable)
- `mrp` / `mrp_inventory` - Manufacturing integration

## Technical Specifications

### Python Syntax: Odoo 18.x Standards
```python
# Modern API patterns used throughout
@api.depends              # Computed fields with store=True where appropriate  
@api.constrains           # Business rule validation
@api.onchange             # Front-end field dependencies
def _compute_xxx(self):   # Read-only computed aggregations
```

### Database Schema
- 10 new models with company multi-support
- 24 security access rules (user + manager tiers)
- 6 CSV data files for catalog seeding  
- Multiple XML report templates
- Custom sequence definition for sale transfers

### Security Model
```csv
# Two-tier approach:
# User Group    → Read-only on product specs
# Manager Group  → Full CRUD + Sale Transfers
model_id          group_id            permissions
pharmadus.product.line.user   base.group_user      |R|
pharmadus.product.line.manager product.group_product_manager  |RCUD|
```

## Version History

### v18.0.1.0.0 (Current) - Odoo 18.0.x
- Product catalog with line/subline hierarchy
- Stock lot creation wizard integrated
- Sale transfer quotation system
- Enhanced purchase reporting with spec fields
- Custom invoice report extensions

## File Structure Overview

```
pharmadus_base/
├── __manifest__.py              # Module registration (installable: True)
├── __init__.py                  # Import registry entry points
├── models/                      # Business logic layer (8 Python files)
│   ├── pharma_product_specification.py    # Catalog mix + 7 specialized models
│   ├── product_template.py              # Extended fields + validation
│   ├── stock_lot.py                     # Lot counting logic
│   ├── sale_transfer.py                 # Custom quotation model (~230 lines)
│   └── ...                                (reports, wizards)
├── views/                       # UI definition (8 XML files)
│   └── product_template_views.xml  # Main spec form integration
├── security/ir.model.access.csv    # ~19 access rules
├── data/*.csv                    # Catalog data seeding (6 files, ~200 records)
├── readme/                      # Documentation
│   ├── DESCRIPTION.md              # This file
│   └── USAGE.md                     # User guide  [NEW]
├── report/*.xml                  # PDF templates (lot labels, transfers)
└── static/src/stock_forecasted/   # JS/Owl widget extensions
```

## Installation Notes

### Manual Installation Steps
1. Enable developer mode (`Settings → Settings`)
2. Upload module via Apps → Install from ZIP or folder drag
3. Click Upgrade to install database records (csv/xml data)  
4. Verify appearance of "Especificaciones" menu entries
5. Check for any Python import errors in logs

### Post-Install Tasks
- Import CSV catalog files manually via: Settings → Configuration → Custom Properties/Fields → CSV Import  
- Create product lines first, then sublines (validation enforces order)
- Assign products to spec fields before creating sale/purchase orders

## Migration from Odoo 16/17

If upgrading from previous version:
```bash
# Backup database first!
odoo-bin -c odoo.conf --upgrade-all-modules
# Then update model references for compatibility with Odoo 18 API
```

---
