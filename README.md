# Tommalo — ERP + sitio web (Odoo 19 en Cloudflare)

> **Estado: base preparada, sin desplegar.** Este repositorio es la base del sistema de Tommalo. No se despliega hasta que
> el cliente tenga su cuenta de Cloudflare pagada. Antes de tocar nada, lee [`CLAUDE.md`](CLAUDE.md) y
> [docs/TOMMALO.md](docs/TOMMALO.md). Lo que falta que decida el cliente: [docs/PENDIENTES_DEL_CLIENTE.md](docs/PENDIENTES_DEL_CLIENTE.md).

## Qué es

Una sola plataforma para una tienda en línea de Panamá: facturación, inventario, ventas, compras, CRM, contabilidad,
nómina, **sitio web con tienda**, programa de puntos (Socios) y de vendedores, más asistentes de IA: **Brian** (para el
equipo, dentro del panel), **Juan** (para los clientes: WhatsApp por la API oficial de Meta y Telegram; Messenger e
Instagram, listos para conectar) y **Sofía** (la asistente del CRM: propone y una persona aprueba). Hecha sobre el
código abierto de **Odoo 19 Community**; corre en **Cloudflare** (Workers, Containers, Durable Objects, R2 y KV).

El sistema viene de D'CASA Panamá (original) y Baby Caleb (copia con ubicación exacta de entrega con mapa). Tommalo
conserva el prefijo técnico `dcasa_` de los módulos para poder traer mejoras; el cliente no lo ve.

- Odoo viene como submódulo (`vendor/odoo`) y **no se modifica nunca**; todo lo propio está en módulos de `addons/`.
- Odoo y PostgreSQL corren en **un** contenedor; la base se respalda sin parar en R2 y se restaura sola al arrancar.
- Todo cambio pasa por pruebas; a producción solo se llega a mano, desde `main`, con el «sí» del cliente.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `vendor/odoo` | Odoo 19.0 (submódulo git fijado a un commit). **No se modifica nunca.** |
| `addons/` | Los módulos propios (prefijo `dcasa_` y `website_dcasa`). Uno por uno: [docs/MODULOS.md](docs/MODULOS.md). |
| `edge/` | Worker de Cloudflare `tommalo` (TypeScript). Contrato con la imagen: [`edge/CONTRATO_CONTENEDOR.md`](edge/CONTRATO_CONTENEDOR.md). |
| `juan/` | Worker del asistente de clientes `tommalo-chatbot` (TypeScript, Durable Objects). [docs/JUAN.md](docs/JUAN.md). |
| `puente-wa/` | Puente de WhatsApp por QR (opcional, no se usa con la API oficial). [docs/JUAN_PUENTE.md](docs/JUAN_PUENTE.md). |
| `docker/` | Imagen de producción (`Dockerfile`), arranque (`entrypoint.sh`), PostgreSQL con pgBackRest (`pg.sh`) y la identidad del negocio (`negocio.env`). |
| `scripts/` | `test.sh` (instala en base limpia y corre las pruebas), respaldo, simulacro de restauración, importar catálogo. |
| `.github/` | Flujos de CI y despliegue (no se lanzan en esta fase), sus scripts y las versiones estables. |
| `fuentes/` y `up media/` | Vacías: el catálogo de Tommalo todavía no se sube ([docs/CATALOGO.md](docs/CATALOGO.md)). |
| `docs/` | Toda la documentación. **[Índice](docs/README.md)**. |

## Comandos

```bash
# Clonar con el submódulo de Odoo
git clone --recurse-submodules --shallow-submodules https://github.com/dcasapty/Tommalo_New_word.git

# Odoo en local (Python)
make setup                  # submódulo + .venv con las dependencias de Odoo
make init DB=dcasa          # crea la base con los módulos y español
make run DB=dcasa           # http://localhost:8069

# Pruebas
scripts/test.sh [modulo1,modulo2]   # instala en base limpia y corre los tests (PostgreSQL: DB_HOST/DB_USER/DB_PASSWORD)
ruff check addons
cd edge && npm ci && npm test && npm run typecheck     # igual en juan/ y puente-wa/
```

## Documentos

| Para… | Leer |
|---|---|
| Entender esta base y qué falta | [docs/TOMMALO.md](docs/TOMMALO.md) · [docs/PENDIENTES_DEL_CLIENTE.md](docs/PENDIENTES_DEL_CLIENTE.md) · [docs/superpowers/ESTADO.md](docs/superpowers/ESTADO.md) |
| Las reglas del repositorio | [CLAUDE.md](CLAUDE.md) |
| Las cuentas y claves para desplegar, paso a paso | [docs/PASO_A_PASO_CLAVES.md](docs/PASO_A_PASO_CLAVES.md) |
| Instalar el sistema para otro negocio | [docs/REPLICAR.md](docs/REPLICAR.md) |
| Cómo se conecta todo | [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) |
| Qué hace cada módulo | [docs/MODULOS.md](docs/MODULOS.md) |
| Desplegar y volver atrás | [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md) · [docs/OPERACION.md](docs/OPERACION.md) |
| Lo que ya falló antes y por qué | [docs/CONTEXTO_AGENTICO.md](docs/CONTEXTO_AGENTICO.md) |
