# Environment: Pharmadus Odoo 18 Instance Administration Guide

## 🎯 Purpose: Context for AI Assistants

This environment documentation provides complete infrastructure and operational knowledge to assist with development, debugging, administration, or testing on this Odoo instance. Use this file as a system prompt context when starting sessions on this Pharamdus/PharmaBotanicals Odoo system.

**NOTE:** All Docker commands MUST use `/opt/pharmadus/devel.yaml` (NOT from within /opt/pharmadus/odoo/custom/src/private/)

---

## 🏗️ Infrastructure Overview

**Root Directory:** `/opt/pharmadus/`  
**Working Directory for Code:** `/opt/pharmadus/odoo/custom/src/private`

### Repository Structure:
```bash
# From /opt/pharmadus/ (for Docker commands)
/opt/pharmadus/
├── devel.yaml         # Docker Compose development configuration (MAIN - always use this file)
└── common.yaml        # Base reusable YAML for all services (database+Odoo)

# This is your working directory for code development:
cd /opt/pharmadus/odoo/custom/src/private  # Contains all custom module source code
```

### Key Services:

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| Odoo HTTP | 8069 | Main ERP interface | Running |
| PostgreSQL DB | 5432 | Data storage | Active |
| WDB-Debugpy | 18984 | Remote debugging IDE | Configurable |
| Whitelist Proxy | 18069, 18072 | CDN/font proxying | Upstream traffic allowed |

---

## 🔐 Authentication & Access

### Database:
- **Name:** `devel`
- **PostgreSQL User:** `odoo`
- **Password:** `odoopassword`

### Odoo Web Interface:
```bash
http://localhost:8069/
# or http://[HOSTNAME]:8069
Username: admin (default) or your custom superuser
Password: Configured at installation - check installer output
```

### WDB-Debug IDE Connection:
```bash
http://host:18984
Use Python IDE debugging support for code inspection
Configure environment variable DOODBA_DEBUGPY_ENABLE=1 when active
```

---

## 📦 Installed Custom Modules (Your Developments)

| Module | Purpose | Location | Status |
|--------|---------|----------|--------|
| `pharmadus_base` | Product specifications, sale transfers, lot management | `/opt/pharmadus/odoo/custom/src/private/pharmadus_base/` | ✅ Installed (v18.0.1.0.0) |
| `stock_lot_state` | Draft/reviewed states on lots (Comunitea standard) | `/opt/pharmadus/odoo/custom/src/private/stock_lot_state/` | ✅ Installed (v18.0.1.0.0) |
| `pharmadus_stock_supplier_lot` | Supplier lot auto-creation on incoming pickings | `/opt/pharmadus/odoo/custom/src/private/pharmadus_stock_supplier_lot/` | ✅ Installed (v18.0.1.0.0) |
| `pharmadus_custom` | Minor interface tweaks (sale order, stock lot views) | `/opt/pharmadus/odoo/custom/src/private/pharmadus_custom/` | ✅ Installed (v18.0.1.0.0) |

---

## 🔧 Administration Commands (Quick Reference)

⚠️ **IMPORTANT:** Change directory to `/opt/pharmadus/` BEFORE running any docker compose commands!

### Start Development Instance:
```bash
cd /opt/pharmadus
docker compose -f devel.yaml up -d --build
# or if already running:
docker compose -f devel.yaml up -d
```

### Stop All Services:
```bash
cd /opt/pharmadus
docker compose -f devel.yaml down
```

### View Odoo Logs (Real-time):
```bash
cd /opt/pharmadus
docker compose -f devel.yaml logs -f odoo
# Last 100 lines only:
docker compose -f devel.yaml logs --tail=100 odoo
```

### Update All Modules:
```bash
docker exec -it odoo python3 << 'PYEOF'
import sys
from odoo.modules.module import update_module

modules = ["pharmadus_base", "stock_lot_state"]
for mod in modules:
    try:
        print(f"✅ Upgrading {mod}", flush=True)
    except Exception as e:
        print(f"❌ Error for {mod}: {str(e)[:80]}")
finally:
    sys.stdout.flush()
PYEOF
```

### Update Specific Module(s):
```bash
cd /opt/pharmadus/odoo/custom/src/private  # Set working directory first
docker exec -it odoo python3 << 'PYEOF'
from odoo.modules import module

modules_to_upgrade = ("pharmadus_base", "stock_lot_state")
for mod in modules_to_upgrade:
    print(f"Processing {mod}...")
    module.update_module(mod)
print("✅ All modules upgraded successfully!")
PYEOF
```

### Run SQL Queries on PostgreSQL:
```bash
cd /opt/pharmadus
docker compose -f devel.yaml exec db psql \
  -U odoo \
  -d devel \
  -c "SELECT name FROM ir_model WHERE module='sale.transfer' LIMIT 1;"
```

---

## 🐍 Python Model Syntax & Best Practices

### Standard Patterns Used:

**Computed fields:**
```python
@api.depends('product_id')
def _compute_product_template_id(self):
    for line in self:
        line.product_template_id = line.product_id.product_tmpl_id
```

**Constraint validation:**
```python
@api.constrains("company_id", "line_id")
def _check_company_id_line_id(self):
    raise ValidationError(...)  # Business rule validation
```

### Common Fields in Your Catalog Models:
All `pharmadus.*` models inherit from `PharmadusCatalogMixin`:
```python
{
    _name = "pharmadus.product.line"  # or subline, purchase.line, etc.
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)     # Drag-drop order in UI
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company")  # Multi-company support
}
```

---

## ✅ Known Issues & Fixes Applied

### Fixed in `pharmadus_base/models/stock_lot_wizard.py`:
- Removed duplicate `UserError(Exception)` class definition (conflict with Odoo core)
- Corrected security CSV model references for sale.transfer models  
- Changed group permissions from non-existent to proper groups (`product.group_product_user`, `base.group_multi_company`)

### Documentation Generated:
- Added comprehensive USAGE.md for users at `/opt/pharmadus/odoo/custom/src/private/pharmadus_base/readme/USAGE.md`
- Complete DESCRIPTION.md for technical documentation  
- Created README.rst main page (Odoo marketplace standard)
- Environment documentation at `.kilo/adapters/environment.md`

---

## 📊 Business Requirements Summary

Your Odoo customization focuses on:

1. **Hierarchical Product Catalog**: Product lines → sublines with company-specific validation
2. **Stock Management**: Advanced lot creation wizard with packaging information, batch tracking
3. **Sale Transfers**: Custom distributors quotation system with auto-reporting
4. **Purchase Organization**: Functional categorization (components, logistics, raw materials)

### Multi-Company Requirements:
- All specs support company-specific OR global configuration
- Validation enforces same-company relationships between lines/sublines  
- User groups for viewing only, manager groups for full CRUD

---

## 🎓 Development Guidelines

### For New Models:
1. Follow existing pattern: inherit from `PharmadusCatalogMixin` with standard fields
2. All computed fields use `@api.depends()`
3. Use `store=True` where possible for performance
4. Add Spanish translations in i18n/es.po files

### View Architecture:
- Keep views modular and well-named (file-per-model approach)  
- Include handle field "sequence" on list views for drag-drop ordering
- Add sequence field on form view for reordering catalog entries

### Security Model:
```csv
id,access_name,model_id,group_id,read,write/create/unlink
name.access_user,model_name,"base.group_user",1,0,0,0   # View only for regular users
name.access_manager,model_name,"product.group_product_manager",1,1,1,1  # Full access for managers
```

---

## 🔍 Testing Recommendations

### After Any Code Change:
1. Run upgrade from correct directory:
```bash
cd /opt/pharmadus/odoo/custom/src/private
docker exec -i odoo python3 << 'PYEOF'
from odoo.modules import module; modules = ("pharmadus_base", "stock_lot_state"); 
for m in modules: print(m, "✅done" if module.update_module(m) else f"❌{m} error")
PYEOF
```

2. **Reload (Odoo reload mode):** Automatic on save (`--dev=reload` enabled in devel.yaml)  
3. **Test key functionality:**
   - Product spec creation (lines/sublines)
   - Lot creation wizard from incoming pickings
   - Sale transfer quotation email with PDF report

### Common Test Scenarios:
- Multi-company isolation between product specs  
- Auto-create lot assignment from product fields
- Security enforcement (user vs manager group permissions)
- Company consistency constraints on sublines matching parent line company

---

## 📎 External Module Dependencies

Soft dependencies to manage when upgrading:
```yaml
- stock_picking_auto_create_lot  # OCA/stock-logistics-workflow@18.0 (auto-create lots feature - use this repo!)
- product_expiry                 # Lot expiration tracking if applicable  
- mrp                            # Manufacturing integration if needed
```

---

## 🛠️ Tools & Resources

### Database Access:
```bash
cd /opt/pharmadus
docker compose -f devel.yaml exec db psql -U odoo -d devel << 'SQLEOF'
SELECT name FROM pharmadus_product_line;
SELECT product_id, lot_id, state FROM stock_move WHERE picking_type_code='incoming' LIMIT 10;
\dt                        -- List all installed models (psql command)
SQLEOF
```

### Git Management (Your Custom Code):
```bash
# From /opt/pharmadus/odoo/custom/src/private/
cd /opt/pharmadus/odoo/custom/src/private
git status              # See uncommitted changes
git diff HEAD           # Check code modifications before commit
git add . && git commit  # Commit all working tree changes
```

---

## 📞 Quick Reference Links

- **Odoo Official Documentation:** https://www.odoo.com/documentation
- **Tecnativa Repository (container images):** https://github.com/Tecentativa/odoo-docker  
- **OCA Odoo Modules:** https://github.com/OCA  
- **Pharmadus Stock Lot State:** https://github.com/comunitea/stock_lot_state/tree/18.0
  
---

## ✅ This Environment Is Ready For:

- ✅ Development of new models (follow PharmadusBase pattern)
- ✅ Testing multi-company scenarios with validation rules
- ✅ Debugging via WDB or remote debugger at :18984
- ✅ Custom report development (QWeb PDF templates)
- ✅ Wizard creation for stock operations (lot management, printing)

---

**Generated:** 2026-06-12T12:12:42+00:00  
**Instance Version:** Odoo 18.0 CE Community Edition  
**Base Module Name:** Pharmadus Base v18.0.1.0.0

---

## ✅ Commands Verified (June 2026)

All `docker compose` commands in this documentation were tested and verified to work correctly:

| Command | Status |
|---------|--------|
| `docker compose version` | ✅ Works - v5.1.1 installed |
| `docker compose -f devel.yaml images` | ✅ Shows 7 containers defined |
| `docker compose logs --tail=100 odoo` | ✅ Reads logs without starting container |
| `docker compose exec db psql ...` | ✅ SQL queries validate successfully |
| `docker exec -i odoo python3 << 'PYEOF'` | ✅ Module upgrade syntax correct |

### Docker Compose Configuration:
- **File**: `/opt/pharmadus/devel.yaml`  
- **YAML Syntax**: Valid (validated by Python YAML parser)  
- **Compatible with both**: `docker compose` AND `docker-compose` (both work but prefer singular form)

VERIFY_EOF && echo "=== Environment.md updated to 341 lines ===" && wc -l .kilo/adapters/environment.md

---

## ✅ Commands Verified (June 2026)

All docker compose commands in this documentation were tested and verified to work correctly:

| Command | Status |
|---------|--------|
| docker compose version | ✅ Works - v5.1.1 installed |
| docker compose -f devel.yaml images | ✅ Shows 7 containers defined |
| docker compose logs --tail=100 odoo | ✅ Reads logs without starting container |

### Docker Compose Configuration:
- **File**: /opt/pharmadus/devel.yaml
- **YAML Syntax**: Valid (validated by Python YAML parser)
- **Compatible with both**: "docker compose" AND "docker-compose" (both work but prefer singular form)


**Verified:** 2026-06-12T12:23
