# Plan: base del sistema de Tommalo

Diseño: [../specs/2026-11-27-base-tommalo-diseno.md](../specs/2026-11-27-base-tommalo-diseno.md). Reglas de limpieza:
[2026-11-27-guia-de-limpieza.md](2026-11-27-guia-de-limpieza.md). Estado vivo: [../ESTADO.md](../ESTADO.md).

## Fases

1. **Moldes y mejoras.** Clonar Baby Caleb y D'CASA (solo lectura), anotar los SHA base, comparar lo que D'CASA tiene
   después de `d2ba8caf` con Baby Caleb y traer lo general. *Hecho:* Baby Caleb ya lo incluye todo.
2. **Copia limpia.** Árbol de Baby Caleb sin historial, sin `fuentes/`, `up media/`, fotos, catálogo, informes ni historia
   de gerencia. *Hecho.*
3. **Nombres propios.** Cloudflare (`tommalo*`), imagen `tommalo-odoo`, buckets `tommalo-production` y `tommalo-staging`,
   sin dominio ni subdominio ajeno, puerta del equipo apagada, campaña apagada. *Hecho.*
4. **Quitar contenido de otros negocios.** Marca (paleta neutra y logo provisional), textos del sitio, páginas de
   marketing, conocimiento del bot, catálogo, datos de la empresa, teléfonos, direcciones, dominios, redes. Por zonas:
   web, resto de módulos Odoo, `dcasa_catalogo`, `juan/` y `puente-wa/`, y el resto (docs, scripts, flujos). *En curso.*
5. **Instalar con catálogo vacío y pasar todas las pruebas** (`scripts/test.sh`, `ruff check addons`, `npm test &&
   npm run typecheck` en `edge/`, `juan/`, `puente-wa/`). Las pruebas se ajustan, no se saltan.
6. **Documentos.** `CLAUDE.md`, `docs/TOMMALO.md`, `PASO_A_PASO_CLAVES.md` (con el bloque de Google Maps),
   `PENDIENTES_DEL_CLIENTE.md`, `MARCA_TOMMALO.md`, `CATALOGO.md`.
7. **Revisión antes de cada push:** `scripts/revisar_datos_ajenos.sh` sin hallazgos duros.
8. **Después (sin decisiones del cliente):** cargador de catálogo de ejemplo (datos inventados y marcados «de prueba»),
   valores de marca centralizados, revisión de seguridad.

## Lo que no se hace en esta fase
Desplegar, lanzar flujos de GitHub, crear recursos o cuentas en Cloudflare, subir el catálogo real, cambiar la
visibilidad del repositorio, pedir o guardar claves.

## Después de la base (cuando el cliente decida)
Cuenta y claves → staging → revisión → producción (`docs/REPLICAR.md` §6) · módulo `dcasa_catalogo_tommalo` · dominio ·
marca definitiva.
