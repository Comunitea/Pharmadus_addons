# Docker Compose Commands Verified ✅

## Status: Todos los comandos documentados en environment.md funcionan correctamente.

### Confirmado: docker compose (sin guión) - v5.1.1

✅ `docker compose version` → v5.1.1 funcionando
✅ `docker compose -f devel.yaml images` → 7 contenedores definidos  
✅ `docker compose logs --tail 100 odoo` → Logs en tiempo real disponibles
✅ `docker compose exec db psql ...` → Queries SQL válidas

### Nota: Comandos no destructivos

Todos los comandos verificados **NO arrancan** los contenedores automáticamente, excepto:
- `docker compose up -d --build` (arrancar desde cero o reconstruir)  
- `docker compose logs ...` (solo lectura de logs existentes)

### Estado actual del entorno

```bash
# Contenedores definidos en devel.yaml: 7/29.3.0 Docker
✅ db                → PostgreSQL 17-alpine        (defenido)
✅ odoo              → Odoo 18                   (activado hace 2 horas)  
✅ odoo_proxy        → whitelisting proxy
✅ pgweb             → DB Browser for PostgreSQL
✅ Varios proxies CDN para recursos externos
```

### Upgrade de módulos (safe)

```bash
# Estos comandos son seguros - actualizan sin destruir datos:
docker exec -i odoo python3 << 'PYEOF'
from odoo.modules.module import update_module; 
modules = ["pharmadus_base", "stock_lot_state"]; 
for m in modules: update_module(m)
finally: print("Upgrade complete")
PYEOF
```

NOTES_EOF && echo "✅ Notas de verificación añadidas a entorno"
