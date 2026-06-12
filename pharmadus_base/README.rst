.. |logo| image:: https://raw.githubusercontent.com/Ipharmadus/odoo/main/logo.png
   :width: 200px

Pharmadus Base Module
=====================

.. image:: https://img.shields.io/badge/version-18.0.1.0.0-blue.svg
           https://img.shields.io/license/AGPL-3.0-or-later.svg

**Base module for Pharmadus-specific customizations in Odoo 18 CE**

.. contents::
   :depth: 2
   :local:

Overview
--------

The Pharmadus Base module provides the foundation for product specification management in Odoo, implementing a comprehensive catalog structure with hierarchical relationships and company-specific constraints. This module serves as the core component for all Pharmadus-specific customizations.

Key Features
------------

- **Hierarchical Product Catalog**:
  - Product Lines → Sublines relationship with validation
  - Support for packaging types, base forms, and garments
  - Purchase-specific product lines and sublines

- **Company-Specific Management**:
  - Multi-company support with strict company validation
  - Company constraints ensure data integrity across organizations

- **Comprehensive Security Model**:
  - Two-tier access control (user vs manager)
  - Read-only access for standard users
  - Full CRUD permissions for product managers

- **Standardized UI Components**:
  - Consistent list and form views across all models
  - Drag-and-drop sequence management
  - Spanish localization for all UI elements

Technical Details
-----------------

Module Structure
~~~~~~~~~~~~~~~

The module follows Odoo's standard structure with the following key components:

.. code-block:: text

   /pharmadus_base/
   ├── __init__.py
   ├── __manifest__.py
   ├── data/                # Data files (CSV, XML)
   ├── models/              # Model definitions
   │   ├── __init__.py
   │   └── pharmacus_product_specification.py
   ├── security/            # Security rules
   │   └── ir.model.access.csv
   ├── views/               # View definitions
   │   └── pharmacus_product_specification_views.xml
   ├── report/              # Report templates
   ├── static/              # Static assets
   └── documentation/       # Documentation files

Models
~~~~~~

The module implements several specialized models that inherit from a common abstract mixin:

.. code-block:: python

   class PharmadusCatalogMixin(models.AbstractModel):
       _name = "pharmadus.catalog.mixin"
       name = fields.Char(required=True, translate=True)
       sequence = fields.Integer(default=10)
       active = fields.Boolean(default=True)
       company_id = fields.Many2one(comodel_name="res.company", string="Compañía")

Specialized models include:

- **Product Hierarchy**:
  - `pharmadus.product.line`: Product lines
  - `pharmadus.product.subline`: Sublines with parent validation

- **Product Characteristics**:
  - `pharmadus.product.packaging.type`
  - `pharmadus.product.base.form`
  - `pharmadus.product.garment`

- **Purchase-Specific**:
  - `pharmadus.product.purchase.line`
  - `pharmadus.product.purchase.subline`

- **Grouping**:
  - `pharmadus.product.grouping`

Security Model
~~~~~~~~~~~~~~

The module implements a two-tier security model:

.. list-table:: Access Control Rules
   :widths: 25 10 10 10 10 10
   :header-rows: 1

   * - Group
     - Model
     - Read
     - Write
     - Create
     - Delete
   * - User (base.group_user)
     - All models
     - ✓
     -
     -
     -
   * - Manager (product.group_product_manager)
     - All models
     - ✓
     - ✓
     - ✓
     - ✓

Installation & Configuration
-----------------------------

Prerequisites
~~~~~~~~~~~~~

- Odoo 18 CE
- PostgreSQL database
- Python 3.7+

Dependencies
~~~~~~~~~~~~

The module depends on several core and custom Odoo modules:

.. code-block:: python

   {
       "depends": [
           "base",
           "mail",
           "sale",
           "purchase",
           "purchase_requisition",
           "stock",
           "account",
           "stock_account"
       ]
   }

Usage
-----

The module integrates with Odoo's standard configuration menus:

- **Sale Module**: Product specifications under "Especificaciones"
- **Purchase Module**: Product specifications under "Especificaciones"
- **Stock Module**: Product specifications under "Especificaciones"

Each section provides access to all catalog models through consistent list and form views.

Development & Customization
---------------------------

The module is designed for extensibility:

1. **Model Extension**:
   - Add new fields by inheriting from existing models
   - Override validation methods as needed

2. **View Customization**:
   - Extend existing views using Odoo's view inheritance
   - Modify form layouts while preserving standard functionality

3. **Security**:
   - Create custom groups by copying existing patterns
   - Add fine-grained access rules as needed

Recommendations
---------------

For optimal performance and maintainability:

1. **Internationalization**:
   - Implement proper translation support for all strings
   - Consider language fallback mechanisms

2. **Performance**:
   - Review sequence handling for large catalogs
   - Optimize database queries for complex relationships

3. **Testing**:
   - Develop comprehensive test cases for multi-company scenarios
   - Create integration tests for catalog operations

4. **Documentation**:
   - Add module-level documentation with setup instructions
   - Document all validation rules and business implications

Support & Contributing
----------------------

For support or contributions:

1. Report issues on the `GitHub repository <https://github.com/Ipharmadus/odoo>`_
2. Follow the existing code style and patterns
3. Submit pull requests with comprehensive test coverage

License
-------

This module is licensed under the AGPL-3.0 license.

.. image:: https://www.gnu.org/licenses/agpl-3.0.svg
   :width: 100px
   :alt: AGPL-3.0 License
