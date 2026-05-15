# Stock Lot State

## Descripción

Este módulo añade estados (Borrador/Revisado) al modelo de lote/número de serie en Odoo 18.

### Características principales

- **Estados de lote**: Los lotes pueden estar en estado "Borrador" o "Revisado"
- **Control de edición**: 
  - Los lotes en estado borrador pueden editarse libremente
  - Los lotes en estado revisado están en modo solo lectura
- **Transición automática**: Los lotes creados en albaranes de compra pasan automáticamente a estado "Revisado" cuando se valida el albarán
- **Seguimiento de revisión**: Registra quién y cuándo revisó cada lote
- **Filtros de búsqueda**: Permite filtrar lotes por estado en las vistas de búsqueda

## Instalación

1. Copiar el módulo en el directorio de addons de Odoo
2. Actualizar la lista de módulos
3. Buscar "Stock Lot State" e instalarlo

## Configuración

No requiere configuración adicional. El módulo funciona automáticamente tras la instalación.

### Permisos

- **Usuarios de inventario** (`stock.group_stock_user`): Pueden ver todos los estados y marcar lotes como revisados
- **Gestores de inventario** (`stock.group_stock_manager`): Adicionalmente, pueden revertir lotes revisados a borrador

## Uso

### Estados de lote

#### Estado Borrador (por defecto)
- Todos los lotes nuevos se crean en estado "Borrador"
- Los lotes en borrador pueden editarse sin restricciones
- Se muestran en gris en la vista de lista

#### Estado Revisado
- Los lotes se marcan automáticamente como revisados al validar albaranes de compra
- También se pueden marcar manualmente usando el botón "Marcar como Revisado"
- Los lotes revisados están en modo solo lectura
- Se muestran en verde en la vista de lista
- Se registra el usuario y la fecha de revisión

### Botones de acción

En el formulario de lote encontrarás:

1. **Marcar como Revisado**: Visible en estado borrador. Cambia el lote a estado revisado y registra el usuario y fecha
2. **Volver a Borrador**: Visible solo para gestores de inventario en estado revisado. Permite volver a editar el lote

### Filtros de búsqueda

En la vista de lista de lotes, puedes usar los filtros:
- **Borrador**: Muestra solo lotes en estado borrador
- **Revisado**: Muestra solo lotes revisados
- **Agrupar por Estado**: Agrupa los lotes según su estado

### Flujo de trabajo típico

1. Se crea un albarán de entrada de compra
2. Se asignan o crean lotes para los productos recibidos (estado: Borrador)
3. Se valida el albarán de compra
4. Los lotes pasan automáticamente a estado "Revisado" y quedan bloqueados para edición
5. Si es necesario modificar un lote revisado, el gestor de inventario debe:
   - Hacer clic en "Volver a Borrador"
   - Editar la información necesaria
   - Hacer clic en "Marcar como Revisado" nuevamente

## Información técnica

- **Versión**: 18.0.1.0.0
- **Categoría**: Inventory/Inventory
- **Autor**: Comunitea
- **Licencia**: AGPL-3
- **Dependencias**: stock

### Modelos extendidos

- `stock.lot`: Añade campos state, reviewed_by, reviewed_date y métodos de transición
- `stock.picking`: Override de button_validate para marcar lotes automáticamente

## Soporte

Para soporte y consultas: https://www.comunitea.com
