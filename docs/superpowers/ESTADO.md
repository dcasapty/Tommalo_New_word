# Estado de la base de Tommalo (se actualiza a medida que avanza)

Rama: `claude/hopeful-cerf-y23p5l` (el repositorio estaba vacío). Última actualización: 2026-11-27, limpiezas terminadas y pruebas corridas.
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

## Probado (resultado real, 2026-11-27)
- Odoo, corrida completa (`scripts/test.sh`, los 37 módulos juntos): 7708 pruebas; la primera vez 5 fallos y 1 error
  (dos fallos eran de mi edición automática de las listas de «prohibido», uno de una llamada rota y tres de un nombre de
  prueba demasiado largo para 360 px). Se corrigieron y se repitieron `dcasa_invoice`, `dcasa_catalogo`, `website_dcasa`,
  `dcasa_tienda_borde` y `dcasa_pago_yappy`: 0 fallos en 1278 pruebas.
- Aviso que queda en el registro, sin fallo contado: en una prueba de navegador de Yappy («atrás» tras el pago) sale
  «Failed to fetch» al cargar traducciones, porque la página se abandona a propósito. Salió igual en las dos corridas.
- `ruff check addons`: sin errores. `edge/` 326/326, `juan/` 2246 (41 saltadas), `puente-wa/` 744/744; `typecheck` limpio
  en los tres. `scripts/tests` (unittest) 22/22.
- `scripts/revisar_datos_ajenos.sh`: sin hallazgos duros (quedan nombres de marca en documentos y listas de «prohibido»).

## No probado
- Flujos de GitHub (CI), imagen Docker, despliegue y todo lo de Cloudflare: no se lanzan en esta fase.
- Las capturas de referencia visual se regeneraron localmente; no se pudo comparar contra el CI.
- `dcasa_comision_web › test_revision4_carrito` falló en una corrida parcial (148 vs 50 consultas) y no en la completa;
  si reaparece, investigar.
- Las pruebas de Brian ↔ Guía y Guía ↔ Nómina necesitan `dcasa_guia` y `dcasa_nomina` instalados juntos.

## Bloqueos
- **No abro el PR (borrador):** `.github/workflows/ci.yml` se dispara solo con cada PR y correría las pruebas completas y
  la imagen Docker. El encargo dice «sin lanzar flujos de GitHub»; la rama queda subida sin PR hasta que la persona o la
  sesión principal acepten esa corrida. Subir la rama no dispara nada.
- Las decisiones del cliente están en [PENDIENTES_DEL_CLIENTE.md](../PENDIENTES_DEL_CLIENTE.md).

## Siguiente paso
1. Revisión de seguridad breve y de valores de marca centralizados (opcional, ya con la base instalable).
2. La persona decide el PR en borrador, si el repositorio pasa a privado y las preguntas de PENDIENTES_DEL_CLIENTE.
