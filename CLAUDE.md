# CLAUDE.md — reglas de este repositorio

> **Regla número 1 de la persona dueña (2026-11-24): responderle SIEMPRE en español**, en palabras sencillas, sin
> jerga, **una pregunta a la vez**. También los avisos cortos de avance y los resúmenes. Nunca pedirle una clave por el
> chat: se le dice *dónde* pegarla (docs/PASO_A_PASO_CLAVES.md). Lo complejo en paneles web se hace con Claude en
> Chrome: se le escriben las instrucciones.

> **Esta es la base de Tommalo** (copia limpia, sin historial, de Baby Caleb con las mejoras de D'CASA). Antes que
> nada, leer `docs/TOMMALO.md`: de dónde sale, qué se quitó, qué está decidido y qué falta. Lo que ahí no esté, no está
> decidido. **No se despliega nada hasta que el cliente tenga su Cloudflare pagado y dé el «sí».**

## Proyecto

ERP + sitio web de **Tommalo** (tienda en línea de Panamá: belleza, hogar y salud; la mercadería la surte un
proveedor de Dropi) sobre **Odoo 19 Community**, preparado para desplegarse en **Cloudflare** (Worker + Container).

## Al empezar una sesión

Leer `docs/TOMMALO.md`, `docs/PENDIENTES_DEL_CLIENTE.md` y `docs/superpowers/ESTADO.md` (qué está hecho, probado y qué
sigue). Si vas a instalar este sistema para otro negocio, sigue docs/REPLICAR.md. Antes de desplegar o tocar el
arranque, el borde o los flujos de GitHub, leer `docs/CONTEXTO_AGENTICO.md` (cada incidente y falla con su causa y su
arreglo; viene de D'CASA y sigue valiendo). Al terminar la sesión, poner al día `docs/superpowers/ESTADO.md`.

## Estructura

- `vendor/odoo` — Odoo 19.0 como submódulo. **No se modifica nunca.** Para
  cambiar comportamiento se hereda desde un módulo en `addons/`.
- `addons/` — módulos propios, prefijo `dcasa_` (o `website_dcasa`). Campos nuevos
  en modelos de Odoo llevan prefijo `dcasa_` (o `l10n_pa_` si es de localización).
- `edge/` — Worker de Cloudflare (TypeScript). La lógica testeable vive en
  `src/routing.ts` y `src/handler.ts`, sin dependencias de Cloudflare.
- `juan/` — Worker de Juan, el asistente de los clientes (TypeScript, Durable Objects).
- `puente-wa/` — puente de WhatsApp por QR para Juan (Worker + Container).
- `docker/` — imagen de producción; `entrypoint.sh` instala/actualiza módulos.
- `scripts/` — pruebas, importación del catálogo, respaldos y simulacro de restauración.
- `fuentes/` y `up media/` — vacías (con su LEEME): el catálogo de Tommalo todavía no se sube.
- `docs/` — documentación; el índice es `docs/README.md`.

## Comandos

- `scripts/test.sh [modulos]` — instala en base limpia y corre tests (PostgreSQL local).
- `make run DB=dcasa` / `make init` / `make update` — ver `Makefile`.
- `cd edge && npm test && npm run typecheck` (igual en `juan/` y `puente-wa/`).
- `ruff check addons`.

## Convenciones Odoo 19

- Vistas `<list>` (no `<tree>`), `invisible="expr"` (no `attrs`), `<chatter/>`.
- Constraints SQL con `models.Constraint(...)` (no `_sql_constraints`).
- `res.users.group_ids` (no `groups_id`). `self.env._('...')` para textos traducibles.
- Tests: `@tagged('post_install', '-at_install')`. Todo cambio lleva test.
- La Guía (`dcasa_guia`, `docs/GUIA.md`): toda pantalla nueva que un administrador deba encontrar se agrega a `data/guia.json` en palabras sencillas; nunca fechas ni montos de impuestos inventados.
- Adjuntos en R2 (`dcasa_adjuntos_r2`, `ir_attachment.location = r2`; `db` sin credenciales): el contenedor
  no tiene disco persistente. Nunca se borran objetos de R2 al desvincular (lo hace un cron a los 45 días).

## Reglas de marca

**La marca de Tommalo está PENDIENTE** (logo, colores y tipografía los decide el cliente: `docs/MARCA_TOMMALO.md`).
Mientras tanto la base usa una paleta neutra provisional (grises) y una «T» como marcador de logo. Reglas fijas:

1. **No inventar contenido**: ni precios, ni cifras, ni testimonios, ni promesas de entrega, pago o garantía.
2. Los valores de marca viven en un solo lugar (variables SCSS de `primary_variables.scss`, `res_company_data.xml`,
   `website_data.xml`): cambiar la marca es cambiar esos valores.
3. Sistema plano, accesible (contraste AA), tipografías autoalojadas (sin Google Fonts).
4. Tuteo, voz cercana; nada de «remate» ni «¡¡CORRE!!».

## Programa de puntos Socios (`dcasa_socios`)

Reglas heredadas del programa de puntos de la plantilla, no negociables:
1. Ninguna cifra fuera de `addons/dcasa_socios/data/puntos.json`; `null`/`PENDIENTE` no se rellena a ojo.
2. No existe columna de saldo: el saldo es la suma de `dcasa.movimiento`.
3. El libro no se edita ni se borra: se corrige con asientos contrarios con motivo.
4. El referido se paga con la primera compra que da puntos; el padrino se escribe una vez.
5. Un cliente y un socio son la misma ficha (`res.partner`), llave = celular.
6. `DCASA_PIN_PEPPER` jamás se rota.

## Programa de vendedores (`dcasa_socios`, ver `docs/VENDEDORES.md`)

1. Las cifras de fábrica viven solo en la sección `vendedores` de `puntos.json` (misma regla que Socios; `null`/`PENDIENTE` no se rellena a ojo). La dueña las ajusta desde Ajustes › Programa de vendedores (Gerencia y administradores): una capa encima, con versión y vigencia hacia adelante (`dcasa.vend.reglas`). El código de vendedores lee siempre `self.env['dcasa.vend.reglas']._vigentes()`, nunca `cargar_reglas()` a pelo; `programaActivo` es el interruptor.
2. Libro propio e inmutable (`dcasa.vend.movimiento`); el saldo es la suma. Correcciones con asiento contrario.
3. Nada se paga por afiliar ni por reclutar; solo por ventas **pagadas**; un solo nivel; un solo patrocinador (se escribe una vez).
4. Un tope o un error del programa **nunca** hace fallar una venta (la comisión corre en un savepoint tras el pago).
5. Canje de externos y efectivo apagados hasta dictamen del abogado y la contadora (`canje.externosHabilitado`, `efectivoHabilitado`); la pantalla de Ajustes los muestra de solo lectura y el servidor los ignora aunque alguien los mande.
6. La escalera de comisión (`comision.escalones`: tasa y tope mensual por lo vendido en 90 días) solo se cambia hacia adelante, nunca retroactiva: desde Ajustes (cada cambio guardado crea una versión nueva con fecha-hora de vigencia y queda en el historial, que no se edita ni se borra) o, para cambiar la fábrica, subiendo la `version` de `puntos.json`. Lo ya acreditado no se recalcula.

## Datos reales de la empresa

Tommalo · Panamá · RUC, dirección, teléfono y correo: **PENDIENTE** (los escribe el dueño en *Ajustes › Empresas*;
el repositorio es público: ahí no van datos de personas ni de contacto).
