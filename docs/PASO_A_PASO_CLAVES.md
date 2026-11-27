# Paso a paso: las cuentas y las claves para desplegar (Tommalo)

Para el dueño, sin tecnicismos. **Todavía no se hace nada de esto:** primero el cliente paga Cloudflare y da el «sí».
Escrito el 2026-11-27 para la base de Tommalo (Workers `tommalo`, `tommalo-staging`, `tommalo-chatbot`). Lo técnico de
cada clave está en `docs/replicar/CUENTAS_Y_SECRETOS.md`. Las partes difíciles de los paneles web se hacen con
**Claude en Chrome**: se le pega el paso y él maneja el panel.

## Antes de empezar: tres reglas

1. **Ninguna clave se escribe en el chat**, ni en un correo, ni en un documento. Se copia de donde sale y se pega directo
   donde va. Claude nunca necesita verla: puede comprobar que quedó puesta sin leerla.
2. **Todas se guardan primero en el gestor de contraseñas** (Bitwarden, 1Password, el de Google…), con su nombre exacto y
   el entorno (`staging` o `production`). Dos **no se pueden cambiar nunca** (`PGBACKREST_CIPHER_PASS` y
   `DCASA_PIN_PEPPER`): si se pierden, se pierden los respaldos o los PIN de los socios.
3. **Staging y producción llevan claves distintas.** La única excepción son las dos de Cloudflare del paso 1 y del paso 4
   (el número de cuenta y la llave del robot), que pueden ser las mismas en los dos.

**Por qué GitHub y no la cuenta de Claude:** el que arma el sistema y lo sube a Cloudflare es un robot que vive en GitHub y
solo ve las llaves guardadas ahí. Las del bot de clientes (su IA, WhatsApp) van después directo en Cloudflare.

**Los Environments de GitHub** (`staging` y `production`, con sus secretos) en un repositorio **privado** exigen un plan de
pago de GitHub; en uno público son gratis. Por eso la visibilidad del repositorio se decide antes
([PENDIENTES_DEL_CLIENTE.md](PENDIENTES_DEL_CLIENTE.md), pregunta 7).

## Paso 1 — El número de la cuenta de Cloudflare (`CLOUDFLARE_ACCOUNT_ID`)

1. Entra a dash.cloudflare.com con la cuenta de Tommalo (la que paga el plan **Workers Paid**).
2. Menú de la izquierda › **Workers & Pages**.
3. A la derecha aparece **Account ID** (32 letras y números). Cópialo al gestor de contraseñas como `CLOUDFLARE_ACCOUNT_ID`.
4. En la misma pantalla se ve el **subdominio de workers.dev** de la cuenta. Ese nombre se anota (no es secreto) y reemplaza
   a `SUBDOMINIO-PENDIENTE` en `edge/wrangler.jsonc`, `juan/wrangler.jsonc` y `puente-wa/wrangler.jsonc` (lo hace Claude).

## Paso 2 — Las dos cajas de respaldos (buckets de R2)

1. **R2 Object Storage** › **Create bucket**.
2. Nombre: `tommalo-staging`. En **Location** elige **Provide a location hint** › **Eastern North America (ENAM)**.
   Storage class: Standard. **Create bucket**.
3. Repite con el nombre `tommalo-production`, también ENAM.
4. No actives acceso público ni reglas de borrado automático en ninguna de las dos.

Los nombres tienen que ser **exactamente** esos: el código los busca así (`R2_BUCKET` en `edge/wrangler.jsonc`).

## Paso 3 — La llave de cada caja (un token de R2 por caja)

Hazlo **dos veces**, una por caja:

1. **R2 Object Storage** › **Manage API tokens** › **Create Account API token**.
2. Nombre: `tommalo-staging` (o `tommalo-production`). Permisos: **Object Read & Write**. En **Specify bucket(s)**: **Apply to
   specific buckets only** y solo esa caja. TTL: Forever. **Create API Token**.
3. La pantalla muestra **Access Key ID** y **Secret Access Key** **una sola vez**. Cópialas ya al gestor como
   `R2_ACCESS_KEY_ID` y `R2_SECRET_ACCESS_KEY` del entorno que corresponda.

## Paso 4 — La llave del robot (`CLOUDFLARE_API_TOKEN`)

1. Arriba a la derecha, el perfil › **My Profile** › **API Tokens** › **Create Token** › **Create Custom Token**.
2. Nombre: `tommalo-github-deploy`. Permisos (Account · el permiso · el nivel): **Workers Scripts** · Edit; **Containers** ·
   Edit; **Account Settings** · Read; **Workers KV Storage** · Edit.
3. **Account Resources**: Include · la cuenta de Tommalo (solo esa). Sin fecha de vencimiento.
4. **Continue to summary** › **Create Token** → cópiala ya (se ve una sola vez) como `CLOUDFLARE_API_TOKEN`.

Si el primer despliegue dice que falta un permiso, el mensaje dice cuál: se agrega a esta misma llave y se relanza. El día
del dominio se le suma *Zone · Workers Routes · Edit* ([DOMINIO.md](DOMINIO.md)).

## Paso 5 — La IA de Brian (`BRIAN_API_KEY`) — proveedor PENDIENTE

El despliegue no arranca sin esta llave, aunque en staging no se use a Brian. **Qué proveedor de IA usa Tommalo lo decide
el cliente** (pregunta 9 de [PENDIENTES_DEL_CLIENTE.md](PENDIENTES_DEL_CLIENTE.md): importa por privacidad, porque algunos
modelos entrenan con las conversaciones y la política de privacidad lo tiene que decir). Cuando decida:

1. Crear en esa cuenta una llave **nueva**, con nombre `tommalo staging` (y otra `tommalo producción`).
2. Copiarla al gestor como `BRIAN_API_KEY`. El nombre del secreto no cambia aunque el proveedor no sea Anthropic.
3. Las tres variables `BRIAN_PROVEEDOR`, `BRIAN_BASE_URL` y `BRIAN_MODELO` dependen del proveedor elegido (ver
   `docs/replicar/CUENTAS_Y_SECRETOS.md`).

## Paso 6 — Las cinco claves que se inventan

En el gestor de contraseñas, **Generar contraseña**: **64 caracteres, solo letras y números**. Una distinta para cada una, y
otras cinco distintas para producción:

| Nombre | Para qué | Ojo |
|---|---|---|
| `PGBACKREST_CIPHER_PASS` | El candado de los respaldos | **Nunca se cambia** |
| `DCASA_PIN_PEPPER` | Protege los PIN de los socios | **Nunca se cambia** |
| `RESPALDO_TOKEN` | Permiso para pedir un respaldo a mano | — |
| `ODOO_ADMIN_PASSWORD` | La clave del usuario `admin` del panel | Con esta se entra la primera vez |
| `ODOO_MASTER_PASSWORD` | La clave maestra de Odoo | Distinta de la de `admin` |

## Paso 7 — Pegar todo en GitHub

1. github.com › el repositorio **Tommalo_New_word** › **Settings** › **Environments** › **New environment** › `staging`.
2. **Environment secrets** › **Add environment secret**, una por una, con el nombre exacto: `CLOUDFLARE_API_TOKEN`,
   `CLOUDFLARE_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `PGBACKREST_CIPHER_PASS`, `RESPALDO_TOKEN`,
   `ODOO_ADMIN_PASSWORD`, `ODOO_MASTER_PASSWORD`, `DCASA_PIN_PEPPER`, `BRIAN_API_KEY`.
3. **Environment variables** › `URL_SITIO` → `https://tommalo-staging.<subdominio>.workers.dev` (sin `/` al final) y las
   tres de Brian del paso 5. **No** crear `CANONICAL_HOST`.
4. Producción (cuando toque): **New environment** › `production` › **Deployment branches and tags** › **Selected branches and
   tags** › regla `main`. Las mismas diez claves con valores de producción y `URL_SITIO` =
   `https://tommalo.<subdominio>.workers.dev` hasta el día del dominio.
5. Avisar a Claude «ya están». Claude revisa que estén los nombres (sin ver los valores) y lanza el despliegue a staging.

## Lo que viene después (no hace falta ahora)

- **La IA del bot de clientes (Juan):** en el panel de Cloudflare › Workers & Pages › `tommalo-chatbot` (y `-staging`) ›
  Settings › Variables and Secrets, el secreto de la IA elegida; y en Odoo, *Conversaciones › Configuración › Ajustes de
  Juan* (proveedor, modelos y precios).
- Las demás claves del bot (WhatsApp, Telegram) van también en el panel de Cloudflare, no en GitHub.
- Opcionales: Telegram de Brian, correo (Resend), la puerta del equipo (Cloudflare Access), Turnstile, **Google Maps**.

## Plantilla para el bloc de notas (sin valores)

Las **etiquetas** son los nombres de las llaves que se crean en Cloudflare. Los **nombres de los secretos no cambian** aunque
digan `DCASA_`: el sistema los busca por ese nombre exacto. Aquí nunca se escriben los valores.

```text
═══ CLOUDFLARE ═══
R2 Token: tommalo-staging          (caja tommalo-staging)
  Access Key ID:                     → GitHub › staging › R2_ACCESS_KEY_ID
  Secret Access Key:                 → GitHub › staging › R2_SECRET_ACCESS_KEY

R2 Token: tommalo-production       (caja tommalo-production)
  Access Key ID:                     → GitHub › production › R2_ACCESS_KEY_ID
  Secret Access Key:                 → GitHub › production › R2_SECRET_ACCESS_KEY

tommalo-github-deploy (la llave del robot)
  Token:                             → GitHub › staging y production › CLOUDFLARE_API_TOKEN
  Account ID:                        → GitHub › staging y production › CLOUDFLARE_ACCOUNT_ID
  Subdomain (workers.dev):           (no es secreto; reemplaza SUBDOMINIO-PENDIENTE en los wrangler.jsonc)

═══ STAGING (GitHub › Environments › staging › secrets) ═══
PGBACKREST_CIPHER_PASS:              (NUNCA se cambia)
DCASA_PIN_PEPPER:                    (NUNCA se cambia)
ODOO_ADMIN_PASSWORD:
ODOO_MASTER_PASSWORD:                (distinta de la de admin)
RESPALDO_TOKEN:
BRIAN_API_KEY:                       (llave NUEVA; proveedor PENDIENTE)
TIENDA_FEED_TOKEN:                   (opcional: caché de páginas)
Variables (no secretas):
  URL_SITIO =
  BRIAN_PROVEEDOR =
  BRIAN_BASE_URL =
  BRIAN_MODELO =

═══ PRODUCCIÓN (GitHub › Environments › production › secrets) ═══
PGBACKREST_CIPHER_PASS:              (NUNCA se cambia)
DCASA_PIN_PEPPER:                    (NUNCA se cambia)
ODOO_ADMIN_PASSWORD:
ODOO_MASTER_PASSWORD:
RESPALDO_TOKEN:
BRIAN_API_KEY:                       (otra llave NUEVA)
TIENDA_FEED_TOKEN:                   (opcional)
Variables (no secretas):
  URL_SITIO =                        (workers.dev hasta el día del dominio)
  BRIAN_PROVEEDOR =
  BRIAN_BASE_URL =
  BRIAN_MODELO =

═══ JUAN, el chatbot (panel de Cloudflare, NO GitHub) ═══
STAGING  → mismo valor en tommalo-staging y en tommalo-chatbot-staging
  JUAN_ODOO_TOKEN:
  JUAN_WORKER_TOKEN:
PRODUCCIÓN → mismo valor en tommalo y en tommalo-chatbot
  JUAN_ODOO_TOKEN:
  JUAN_WORKER_TOKEN:
Clave de la IA del bot:              → tommalo-chatbot (y -staging)
TELEGRAM_BOT_TOKEN_JUAN:             (bot NUEVO) → tommalo-chatbot
TELEGRAM_WEBHOOK_SECRET_JUAN:        → tommalo-chatbot

═══ PUERTA DEL EQUIPO (opcional, después; GitHub › cada entorno) ═══
DCASA_PUERTA_RUTA:
DCASA_ACCESS_EQUIPO:
DCASA_ACCESS_AUD:                    (= el Application Audience (AUD) Tag de Cloudflare)
DCASA_PUERTA_SECRETO:                (distinto por entorno)

═══ TELEGRAM BRIAN (opcional, después; bot NUEVO) ═══
TELEGRAM_BOT_TOKEN:                  → GitHub › cada entorno
BRIAN_TELEGRAM_SECRETO:              → GitHub › cada entorno
ID OWNER TELEGRAM:                   → panel de tommalo: BRIAN_TELEGRAM_CHATS y DCASA_ALERTA_TELEGRAM_CHAT

═══ MAPAS (Google) — opcional: ubicación exacta de entrega (docs/UBICACION.md) ═══
GOOGLE_MAPS_CLAVE_NAVEGADOR:         → panel de Cloudflare › Worker tommalo (y tommalo-staging) › Variables
                                       (se ve en la página: es normal; en Google Cloud se limita a los sitios de la tienda
                                       y a la API «Maps JavaScript»)
GOOGLE_MAPS_CLAVE_SERVIDOR:          → panel de Cloudflare › Worker tommalo (y tommalo-staging) › Secretos
                                       (secreta; en Google Cloud se limita solo a la API «Geocoding»)
```

Para el **primer despliegue a staging** solo hacen falta el bloque de Cloudflare y el de STAGING. Lo demás va después.
Sin las claves de Google Maps todo sigue funcionando (GPS y dirección escrita); solo no se ve el mapa ni se llena la calle
([UBICACION.md](UBICACION.md)). Todo lo que se inventa o se crea en una cuenta es **nuevo**: nada se reusa de otros negocios.
