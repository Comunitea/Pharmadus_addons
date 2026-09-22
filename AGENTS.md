# Project Instructions

Este repositorio usa skills locales en la carpeta `.skills/`.

Antes de trabajar en tareas relacionadas con Odoo, addons, vistas XML, CSV de datos, modelos ORM, migraciones o actualización de módulos, revisa y aplica primero la skill más adecuada disponible en `.skills/`.

Skills locales prioritarias:

- `.skills/odoo-18.0/SKILL.md`: referencia general de desarrollo Odoo 18.
- `.skills/odoo-dev/SKILL.md`: contexto operativo del entorno local Pharmadus, Docker Compose, Doodba, puertos, base de datos y comandos seguros.
- `.skills/project-graph/SKILL.md`: grafo estructural regenerable de addons, dependencias, modelos, vistas, menús, acciones y datos.

Reglas de uso:

- Para cualquier cambio funcional o técnico en addons Odoo, usa primero la referencia de `.skills/odoo-18.0/`.
- Para cualquier operación sobre esta instancia local, actualización de módulos, logs, contenedores, base de datos o validaciones del entorno, usa también `.skills/odoo-dev/SKILL.md`.
- Para cambios no triviales en manifests, modelos, vistas XML, menús, acciones, seguridad o datos CSV, consulta `.skills/project-graph/SKILL.md` y mantén actualizado su grafo.
- Si cambias cualquier `__manifest__.py`, modelo Odoo, XML de vistas/datos/seguridad, CSV de addons o añades/eliminas/renombras addons, ejecuta `python3 .skills/project-graph/scripts/build_project_graph.py` antes de finalizar y conserva los archivos generados.
- Si hay discrepancias entre una skill y el código real del repositorio, prevalece el código del repositorio.

## Carga de estas skills en DSH

El agente DSH **no descubre skills en el servidor**: su proveedor de skills lee el sistema
de ficheros local (`~/.dsh/skills` y `<projectRoot>/.dsh/skills`), por lo que lo que esté
en `.skills/` no se autocarga. Para que las tres skills del repo se carguen solas, se
copian al espejo local del workspace:

```text
%USERPROFILE%\.dsh\remote\<hostId>\<ruta remota en base64>\.dsh\skills\
    |-- odoo-18/SKILL.md
    |-- odoo-dev/SKILL.md
    `-- project-graph/SKILL.md
```

### Sincronizar (un solo comando)

La implementación versionada es `.skills/tools/sync-to-dsh.ps1`. Se ejecuta desde la
máquina local, cuya clave `~/.ssh/id_ed25519_dsh_sync` está autorizada en el
`authorized_keys` del servidor (usuario `odoo`, host `192.168.192.103`):

```powershell
pwsh -File "$env:USERPROFILE\.dsh\tools\sync-pharmadus-skills.ps1"              # sincroniza
pwsh -File "$env:USERPROFILE\.dsh\tools\sync-pharmadus-skills.ps1" -Mode Check # solo comprueba (exit 1 si hay drift)
```

El lanzador local descarga este script del repo por SSH y lo ejecuta, de modo que la lógica
vive solo aquí. El script compara el `sha256` del origen con el anotado en el banner de
cada copia, verifica además que el cuerpo no se ha alterado y reescribe solo lo que no
cuadra (UTF-8 sin BOM).

Reglas:

- Cada copia local empieza con un banner HTML que registra el `sha256`, el tamaño y la
  fecha del fichero de origen; sirve para detectar copias desactualizadas.
- Si modificas cualquier `SKILL.md` de `.skills/`, **resincroniza las copias locales en la
  misma sesión**; si no, DSH seguirá autocargando la versión antigua.
- Toda skill de `.skills/` debe empezar por frontmatter YAML con `name` (kebab-case) y
  `description`; sin él el cargador la descarta (era el caso de `project-graph`).
- La versión autoritativa es siempre la de este repositorio, nunca la copia local.
