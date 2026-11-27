# Marca de Tommalo (PENDIENTE)

Tommalo todavía no dio logo, colores ni tipografía. No hay archivo de logo (las fotos antiguas del proveedor llevan la
marca «TOMMALO.CO», que no sirve de logo). **No se inventa una marca.** Mientras tanto la base usa un marcador neutro.

## Qué hay hoy (provisional)

| Qué | Valor provisional | Dónde cambiarlo |
|---|---|---|
| Logo | Una «T» blanca en círculo gris oscuro (marcador) | `addons/dcasa_base/static/img/logo.png`, y luego `python scripts/iconos_de_la_marca.py` regenera los íconos y el favicon |
| Colores del sitio y del panel | Grises neutros (texto `#262626`, fondo `#FAFAFA`, acento `#D4D4D4`) | `addons/website_dcasa/static/src/scss/primary_variables.scss`, `addons/dcasa_base/static/src/scss/primary_variables.scss` |
| Colores de los documentos | `#262626` y `#D4D4D4` | `addons/dcasa_base/data/res_company_data.xml` (en una base instalada: *Ajustes › Empresas*) |
| Colores y logo del panel de Odoo | Ajustes | *Ajustes › Marca del panel* ([MARCA_DEL_PANEL.md](MARCA_DEL_PANEL.md)), sin tocar archivos |
| Tipografía | Montserrat e Inter (libres, autoalojadas) | `addons/*/static/src/fonts` |
| Nombre | Tommalo | `addons/website_dcasa/data/website_data.xml`, `res_company_data.xml` |

## Cuando el cliente decida

1. Subir el logo (PNG con fondo transparente) y correr `python scripts/iconos_de_la_marca.py`.
2. Poner sus colores en las variables de arriba (contraste AA: las pruebas lo vigilan) y en la empresa.
3. Regenerar las referencias visuales a propósito, en el mismo cambio (`scripts/actualizar_referencias_visuales.sh`).
