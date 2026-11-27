# Estado de la base de Tommalo (se actualiza a medida que avanza)

Rama: `claude/hopeful-cerf-y23p5l` (el repositorio estaba vacío). Última actualización: 2026-11-27, en curso.
Diseño y plan: [specs](specs/2026-11-27-base-tommalo-diseno.md) · [plan](plans/2026-11-27-plan-base-tommalo.md).

## Hecho
- Moldes clonados (solo lectura) y SHA base anotados (docs/TOMMALO.md). Revisión de D'CASA vs Baby Caleb: Baby Caleb ya
  incluye todo lo de D'CASA posterior a `d2ba8caf`, salvo un aumento de versión de despliegue que no aplica.
- Base copiada de Baby Caleb sin historial, sin fotos, catálogo, `fuentes/`, `up media/`, informes ni historia de otros negocios.
- Nombres de Cloudflare propios (`tommalo*`, buckets, imagen), sin dominio, subdominio `subdominio-pendiente`.
- Colores de marca de otros negocios sustituidos por una paleta gris neutra; logo provisional («T»), no inventado como marca.
- Catálogo vacío (`catalogo.json` sin productos) con las categorías Belleza, Hogar, Salud y Otros.
- Documentos: CLAUDE.md, README, docs/README, TOMMALO, MARCA_TOMMALO, CATALOGO, DOMINIO, LEEME_PRIMERO, PRIORIDADES,
  PASO_A_PASO_CLAVES (con bloque MAPAS), PENDIENTES_DEL_CLIENTE, diseño y plan.
- `scripts/revisar_datos_ajenos.sh` (revisión antes de cada push) y `scripts/cargar_catalogo_ejemplo.py` (catálogo de
  EJEMPLO inventado, marcado «de prueba», nunca en producción).
- Versiones estables: las de D'CASA se quitaron (apuntaban a su registro); marcador `pendiente`.

## Probado (resultado real)
- `edge/`: `npm test` 326/326 y `npm run typecheck` sin errores (2026-11-27).
- `scripts/tests` (unittest): 22/22.
- `dcasa_base` solo (scripts/test.sh): instaló; 2 fallas que dependen de otros módulos instalados
  (`test_exportar … campo cerrado a Gerencia`, `test_aviso_vendedora … sin asunto`): se confirman en la corrida completa.

## No probado
- La corrida completa de `scripts/test.sh` (todos los módulos) y `ruff check addons` (hay E501 por los reemplazos).
- `juan/` y `puente-wa/` (`npm test && npm run typecheck`): los limpia otra tarea en paralelo.
- Los flujos de GitHub (no se lanzan en esta fase), la imagen Docker, el despliegue y todo lo de Cloudflare.
- Las capturas de referencia visual: si cambian, se regeneran localmente y no se pudo comparar contra el CI.

## En curso (agentes en paralelo)
Limpieza de contenido de otros negocios en: sitio web y módulos de tienda; resto de módulos Odoo; `dcasa_catalogo`;
`juan/` y `puente-wa/`.

## Bloqueos
- **No abro el PR (borrador) todavía:** `.github/workflows/ci.yml` se dispara solo con cada PR (`pull_request`) y correría
  las pruebas completas (unos 27 minutos y la imagen Docker). El encargo dice «sin lanzar flujos de GitHub», así que la
  rama queda subida sin PR hasta que el cliente o la sesión principal digan si se acepta esa corrida. Subir la rama no
  dispara nada (`push` solo en `main`). Nota: no desactivé el CI para evitarlo (no fue lo pedido).
- Ninguno técnico. Las decisiones del cliente están en [PENDIENTES_DEL_CLIENTE.md](../PENDIENTES_DEL_CLIENTE.md).

## Siguiente paso
1. Que terminen las limpiezas por zona; correr `scripts/revisar_datos_ajenos.sh` hasta que no haya hallazgos duros.
2. Corrida completa de pruebas (Odoo, tres Workers, ruff); corregir.
3. Primer commit limpio y push; PR en borrador.
