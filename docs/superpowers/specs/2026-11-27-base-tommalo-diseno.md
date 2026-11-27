# Base del sistema de Tommalo — diseño corto

Fecha: 2026-11-27 · Estado: en marcha (sin esperar aprobación para la base limpia).

## Qué es
Tommalo es una tienda en línea de Panamá (belleza, hogar, salud; la mercadería la surte un proveedor de Dropi).
Usa el mismo sistema de D'CASA y Baby Caleb: Odoo 19 Community + sitio y tienda + Socios + asistentes (Juan, Andrés,
Brian, Sofía), todo sobre Cloudflare (Worker + Container + R2). Este repositorio es **solo la base**: no se despliega
hasta que el cliente pague Cloudflare.

## De dónde sale (molde y SHA base)
| Molde | Repositorio | SHA base (HEAD al copiar) |
|---|---|---|
| Baby Caleb (molde principal) | `juanarrietabusiness-pixel/System-Baby-Cale` | `7739044df878c1619054ef6ea1b46aad1ad75bdd` |
| D'CASA (original) | `dcasapty/D_Casa_new_word` | `d928a82e500400fe933a9251ae9a63cf0ee325a9` |
| Último commit compartido de ambos | | `d2ba8caf` |

Baby Caleb ya trae todo lo de D'CASA y además `dcasa_ubicacion` (ubicación exacta de entrega con mapa) y los
ajustes por negocio (ITBMS, tienda física, conocimiento del bot). Revisión de lo que D'CASA tiene después de
`d2ba8caf` (3 commits, #130, #131 y #138): Baby Caleb ya lo incluye todo (203 de 306 archivos idénticos; el resto
difiere solo por marca y textos). Lo único que **no** se trae: el aumento de versión `19.0.1.1.1` de
`dcasa_pago_tilopay` (#138), un truco de despliegue de D'CASA para forzar una imagen nueva; no cambia comportamiento.
Para traer mejoras futuras: comparar contra estos SHA (`git diff <SHA base>..<SHA nuevo>` en cada molde).

## Qué se hizo distinto (la base limpia)
- **Sin historial** de los moldes: primer commit limpio, para no arrastrar datos de otros clientes.
- **Sin** catálogos, fotos, `fuentes/`, `up media/`, logos, precios, cifras, direcciones, teléfonos, dominios ni datos
  de D'CASA o Baby Caleb. Lo no decidido queda vacío o `PENDIENTE`.
- **Prefijo `dcasa_`** se queda (REPLICAR §4.2): permite traer mejoras de los moldes.
- **Cloudflare**: nombres propios (`tommalo`, `tommalo-staging`, `tommalo-chatbot`, `tommalo-puente-wa`,
  `tommalo-odoo`, buckets `tommalo-production` y `tommalo-staging`). Sin `routes` (sin dominio), subdominio
  `workers.dev` como `SUBDOMINIO-PENDIENTE`. Ninguna cuenta ni dominio ajeno.
- **Catálogo vacío**: instala sin productos. Las cuatro categorías (Belleza, Hogar, Salud, Otros) son las del proveedor.
- **Páginas de marketing de Baby Caleb** (beneficios, historia, tips, cómo comprar, FAQ, testimonios) quitadas: eran
  su contenido. Tommalo las escribe cuando decida su mensaje.
- **Marca provisional neutra**: los valores de marca (nombre, colores, tipografías, logo) están centralizados y
  marcados `PENDIENTE` (docs/MARCA_TOMMALO.md). No hay logo: no se inventa.
- **Identidad del negocio** (`docker/negocio.env`): ITBMS, tienda física y conocimiento del bot quedan en un valor
  seguro y reversible hasta que el cliente decida (ver docs/PENDIENTES_DEL_CLIENTE.md).

## Qué falta que decida el cliente
Ver `docs/PENDIENTES_DEL_CLIENTE.md` (en lenguaje sencillo).

## Qué no se hace en esta fase
Sin despliegues, sin lanzar flujos de GitHub, sin crear recursos ni cuentas en Cloudflare, sin subir el catálogo real
(repositorio público), sin claves.
