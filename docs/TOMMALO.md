# Tommalo: de dónde sale esta base y qué está decidido

Tommalo es una tienda en línea de Panamá (belleza, hogar y salud). Un proveedor de Dropi surte la mercadería
(`TOMMALO-PANAMA` en Dropi). Este repositorio es **solo la base**: se prepara todo y **no se despliega** hasta que el
cliente pague Cloudflare.

## De dónde viene (SHA base, para traer mejoras después)

| Molde | Repositorio | SHA base |
|---|---|---|
| Baby Caleb (principal) | `juanarrietabusiness-pixel/System-Baby-Cale` | `7739044df878c1619054ef6ea1b46aad1ad75bdd` |
| D'CASA (original) | `dcasapty/D_Casa_new_word` | `d928a82e500400fe933a9251ae9a63cf0ee325a9` |
| Último commit compartido | | `d2ba8caf` |

Primer commit limpio: sin historial de los moldes, para no arrastrar datos de otros clientes. Para traer mejoras:
`git diff <SHA base>..<SHA nuevo>` en el molde, y se aplican a mano o con `git apply` descartando lo que traiga
datos de ese negocio (REPLICAR.md §8). Detalle de lo revisado: [superpowers/specs](superpowers/specs/2026-11-27-base-tommalo-diseno.md).

## Qué se hizo

- Nombres de Cloudflare propios: Workers `tommalo`, `tommalo-staging`, `tommalo-chatbot(-staging)`,
  `tommalo-puente-wa(-staging)`, repositorio de imagen `tommalo-odoo`, buckets `tommalo-production` y `tommalo-staging`.
  Sin dominio (`"routes": []`) y subdominio `workers.dev` como `SUBDOMINIO-PENDIENTE`. Nada de cuentas ni dominios ajenos.
- Catálogo vacío: la instalación no carga productos. Categorías: Belleza, Hogar, Salud y Otros (las del proveedor).
- Sin páginas de marketing de otros negocios (beneficios, historia, tips, preguntas frecuentes, testimonios).
- Marca provisional neutra: [MARCA_TOMMALO.md](MARCA_TOMMALO.md).
- Prefijo técnico `dcasa_` conservado (REPLICAR.md §4.2).

## Decisiones

| Tema | Estado |
|---|---|
| Nombre | **Tommalo** (así se escribe) |
| Repositorio | Público por ahora; el cliente decide si pasa a privado (pregunta 7 de [PENDIENTES_DEL_CLIENTE.md](PENDIENTES_DEL_CLIENTE.md)) |
| Todo lo demás (ITBMS, tienda física, desde dónde despacha, logo, colores, precios, dominio) | **PENDIENTE**: [PENDIENTES_DEL_CLIENTE.md](PENDIENTES_DEL_CLIENTE.md) |

Los interruptores de identidad están en `docker/negocio.env` con un valor seguro y reversible hasta que el cliente decida.
