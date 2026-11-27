# Versiones estables (a dónde volver si algo se rompe)

Cada vez que una versión queda en producción y el cliente confirma que se ve bien, se agrega aquí y en
`.github/versiones_estables.json` (y su nombre en las opciones de `.github/workflows/volver-a-estable.yml`).

> **Tommalo todavía no tiene versiones estables propias** (no hay despliegues). La entrada `pendiente` del JSON es un
> marcador: el botón «Volver a una versión estable» se niega a usarlo (pide un SHA y un digest de verdad). Las versiones
> estables de los negocios anteriores apuntan a imágenes de **sus** cuentas de Cloudflare, que no existen en la de
> Tommalo: por eso se quitaron. No uses el botón antes de tener la primera versión propia.

## Las versiones guardadas

| Versión | Desde | Qué trae | Código | `app_version` | `imagen_digest` |
|---|---|---|---|---|---|
| (ninguna todavía) | | | | | |

Qué se guarda de cada una:

- **El código:** una rama con su nombre (`estable-AAAA-MM-DD`) que no se toca, hecha desde `main` con el PR ya unido
  (mismo código; desde las sesiones de Claude no se pueden crear etiquetas de git). La Estable 3 y la 4 no tienen rama
  propia: su código es un commit de `main` (`700c34a` y `c378382`), que ya no cambia (`main` solo avanza). El commit exacto con que se
  construyó la imagen es el `app_version` y queda guardado en su PR.
- **La imagen ya construida y probada:** en el registro de Cloudflare, con la etiqueta `dcasa-odoo:<app_version>`.
  No se reconstruye nada para volver. Ningún flujo de este repositorio la borra; cuánto la guarda Cloudflare por su
  cuenta **no está confirmado**.
- **Los datos:** no se guardan «con la versión». Los cuidan los respaldos: cualquier minuto de los **últimos 7 días**
  (pgBackRest), una copia por día de los **últimos 30 días** y la copia anual de cierre (`docs/OPERACION.md`).

## Cómo volver a una versión estable

**Con el botón** (sin copiar nada): Actions → **Volver a una versión estable** → *Run workflow*, en `main`:

- `entorno`: `production` (o `staging` para ensayar primero);
- `version`: la de la tabla (la más nueva arriba: `estable-4`);
- `respaldo_previo`: marcado (desmarcarlo solo si el sitio está caído y el respaldo no puede hacerse).

Llama al mismo flujo *Desplegar*: el último paso espera a que responda esa versión con la base al día y la vigila 600 s
antes de confirmar (`.github/scripts/esperar_salud.sh`), así que cuenta unos 15 minutos, como un despliegue normal. Los
datos de cada versión viven en `.github/versiones_estables.json` (una prueba de CI revisa que estén bien escritos).

**A mano** (si el botón todavía no está en `main`): Actions → **Desplegar** → *Run workflow*, en `main`, con el mismo
`entorno` y `respaldo_previo` y el `app_version` y el `imagen_digest` de la tabla.

**Si un día Cloudflare ya no tuviera la imagen:** lanzar **CI/CD** sobre la rama `estable-AAAA-MM-DD` con
`desplegar_en = staging` (reconstruye y prueba la misma versión) y después desplegar a producción ese commit con el
digest de su resumen, como siempre.

**Qué pasa con los datos.** Hay dos maneras, y se elige según el problema:

1. **Volver solo el programa (lo normal):** las ventas, facturas, clientes y todo lo que se hizo después **se quedan**.
   Lo que solo existía en las versiones nuevas (campos o pantallas que la estable no tiene) deja de verse y sus datos
   se pierden. Si la versión estable es **anterior** al candado «nunca hacia atrás» (la Estable 1 lo es), la base se
   ajusta sola al arrancar. La Estable 2 ya trae el candado: volver a ella desde una versión más nueva pide
   `DCASA_PERMITIR_BAJAR`. Si es **posterior**, el arranque se niega a bajar la base y hay que pegar en el panel de
   Cloudflare del Worker `DCASA_PERMITIR_BAJAR=<su app_version>` antes de desplegar (y quitarla después).
2. **Volver todo a un momento (programa y datos):** solo si un cambio **dañó datos**. Se pierde todo lo hecho después
   de ese momento: decisión de la dueña. Es una sola operación: `DCASA_RESTAURAR_HASTA` con la hora y, en el mismo
   arranque, el despliegue de la versión estable (`docs/OPERACION.md`, «Volver atrás un despliegue»).

**Antes de necesitarlo:** ensayarlo en staging (desplegar ahí la versión estable y abrir Inicio, Conversaciones y una
cotización). Mientras no se haya ensayado, volver puede dar sorpresas (p. ej. un módulo que la versión nueva instaló y
la vieja no conoce). La Estable 3 y la 4 ya se ensayaron (ver la tabla); la 1 y la 2, nunca.

**Juan va aparte.** El botón vuelve Odoo y el borde (`dcasa`); el Worker de Juan (`dcasa-juan`) se despliega con
*Desplegar Juan* desde la rama o el commit que se quiera. La versión de Juan de cada estable está en su fila («Juan
hasta Desplegar Juan N»); para volver Juan, lanzar *Desplegar Juan* (`production`, `dry_run` sin marcar) sobre ese
commit de `main`.

## Cómo se agrega una versión estable

Cuando un despliegue a producción queda «Confirmado» y la dueña dice que se ve bien:

1. Crear la rama `estable-AAAA-MM-DD` desde `main` (ya con el PR unido), o anotar el commit de `main` si no se puede
   crear la rama desde la sesión.
2. Agregar la versión a `.github/versiones_estables.json` (con el `app_version` y el `imagen_digest` del resumen del
   despliegue) y su nombre a las opciones de `version` en `.github/workflows/volver-a-estable.yml`.
3. Agregar la fila a la tabla de arriba y anotarlo en la bitácora (`docs/LEEME_PRIMERO.md`).
4. Ensayarla en staging con el botón (`entorno: staging`) y anotar el resultado en su fila.
