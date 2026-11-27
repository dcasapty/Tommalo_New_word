# Documentación de Tommalo

Índice de lo que hay en `docs/`. Esta base viene de D'CASA y Baby Caleb: los documentos técnicos (módulos, Worker,
despliegue, incidentes) describen el sistema y siguen valiendo; **donde mencionen «la dueña» o un negocio anterior, son
historia de la plantilla**. Lo propio de Tommalo está en los primeros tres.

| Quiero… | Leer |
|---|---|
| Saber de dónde sale esta base, qué se quitó y qué está decidido | [TOMMALO.md](TOMMALO.md) |
| Ver **qué falta que decida el cliente** (en palabras sencillas) | [PENDIENTES_DEL_CLIENTE.md](PENDIENTES_DEL_CLIENTE.md) |
| Ver qué está hecho, qué se probó y qué sigue | [superpowers/ESTADO.md](superpowers/ESTADO.md) · [diseño](superpowers/specs/2026-11-27-base-tommalo-diseno.md) · [plan](superpowers/plans/2026-11-27-plan-base-tommalo.md) |
| Crear las cuentas y pegar las claves, paso a paso | [PASO_A_PASO_CLAVES.md](PASO_A_PASO_CLAVES.md) · [replicar/CUENTAS_Y_SECRETOS.md](replicar/CUENTAS_Y_SECRETOS.md) |
| Cambiar la marca (logo, colores, tipografía) | [MARCA_TOMMALO.md](MARCA_TOMMALO.md) · [MARCA_DEL_PANEL.md](MARCA_DEL_PANEL.md) |
| Cargar el catálogo (cuando se decida) | [CATALOGO.md](CATALOGO.md) |
| El dominio propio | [DOMINIO.md](DOMINIO.md) · [DESPLIEGUE.md](DESPLIEGUE.md) |
| Instalar este sistema para otro negocio | [REPLICAR.md](REPLICAR.md) · [replicar/VALORES_DE_LA_EMPRESA.md](replicar/VALORES_DE_LA_EMPRESA.md) |
| Cómo se conecta todo (Cloudflare, tablas, variables) | [ARQUITECTURA.md](ARQUITECTURA.md) |
| Qué hace cada módulo | [MODULOS.md](MODULOS.md) |
| Roles, permisos, interruptores y políticas del sitio | [PERMISOS.md](PERMISOS.md) |
| Desplegar, volver atrás, operar, costos y respaldos | [DESPLIEGUE.md](DESPLIEGUE.md) · [OPERACION.md](OPERACION.md) · [VERSIONES_ESTABLES.md](VERSIONES_ESTABLES.md) |
| Qué falló antes, por qué y cómo se arregló | [CONTEXTO_AGENTICO.md](CONTEXTO_AGENTICO.md) |
| Seguridad de acceso, doble factor y la puerta del equipo | [SEGURIDAD_ACCESO.md](SEGURIDAD_ACCESO.md) · [PUERTA_MASTER.md](PUERTA_MASTER.md) |

## Por tema

- **Ventas y bodega:** [CATALOGO.md](CATALOGO.md) · [BARRAS.md](BARRAS.md) · [EXISTENCIAS.md](EXISTENCIAS.md) · [ENVIOS.md](ENVIOS.md) · [UBICACION.md](UBICACION.md) · [ROTACION.md](ROTACION.md) · [MOVIMIENTO.md](MOVIMIENTO.md)
- **Clientes y programas:** [CONTACTOS.md](CONTACTOS.md) · [SOCIOS.md](SOCIOS.md) · [VENDEDORES.md](VENDEDORES.md) · [COMISION_WEB.md](COMISION_WEB.md)
- **Asistentes:** [BRIAN.md](BRIAN.md) · [BRIAN_TIENDA.md](BRIAN_TIENDA.md) · [JUAN.md](JUAN.md) · [JUAN_ODOO.md](JUAN_ODOO.md) · [JUAN_CANALES.md](JUAN_CANALES.md) · [JUAN_PUENTE.md](JUAN_PUENTE.md) · [SOFIA.md](SOFIA.md) · [CAMILA.md](CAMILA.md) · [GUIA.md](GUIA.md)
- **Pagos y correo:** [TILOPAY.md](TILOPAY.md) · [YAPPY.md](YAPPY.md) · [CORREO.md](CORREO.md) · [META_CATALOGO.md](META_CATALOGO.md) · [META_EVENTOS.md](META_EVENTOS.md)
- **Contabilidad y personal:** [CONTABILIDAD.md](CONTABILIDAD.md) · [DECISIONES_CONTABLES.md](DECISIONES_CONTABLES.md) · [CONSOLIDACION.md](CONSOLIDACION.md) · [NOMINA.md](NOMINA.md) · [FACTURA_ELECTRONICA.md](FACTURA_ELECTRONICA.md) · [EQUIPO.md](EQUIPO.md) · [MIGRACION.md](MIGRACION.md)
- **Interfaz:** [MARKETING.md](MARKETING.md) · [COLOR_CANTIDAD_CARRITO.md](COLOR_CANTIDAD_CARRITO.md)

## Cómo se mantiene

- Una sola fuente por tema; si un dato aparece en dos documentos, uno enlaza al otro.
- Los datos de personas (nombres, correos, celulares) viven solo en Odoo, nunca aquí. **El repositorio es público.**
- Cifras con fecha. No se inventa contenido: lo no decidido queda `PENDIENTE`.
- Al terminar una sesión se pone al día [superpowers/ESTADO.md](superpowers/ESTADO.md).
