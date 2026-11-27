# Guía de limpieza de la base de Tommalo (para quien edita el código)

Tommalo = tienda en línea de Panamá (belleza, hogar, salud; mercadería de un proveedor de Dropi). El código viene de
Baby Caleb (pañales y bebés) que viene de D'CASA (muebles, La Chorrera). Hay que dejarlo **genérico**: ningún dato,
texto, foto, cifra ni nombre propio de esos dos negocios. Lo no decidido queda vacío o `PENDIENTE`; no se inventa
contenido.

## Reglas
1. Quitar: pañales, bebés, mamás, Nateen, Dany, Velvee, fulares, tallas RN–XXL, toallitas; muebles, colchones, camas,
   salas, comedores, combos cama + colchón (el mecanismo de combos puede quedar, sin datos), La Chorrera,
   Libertadores, Panamá Oeste como zona de entrega, «D'CASA», «Baby Caleb», teléfonos, RUC, direcciones, dominios,
   cuentas de redes, horarios, testimonios, cifras. Ya se reemplazó mecánicamente «Baby Caleb» → «Tommalo»,
   dominios → `tommalo.example`, teléfonos → `6000-0001` / `6000-0002`: revisa que las frases queden con sentido.
2. Valores de ejemplo en pruebas: celular `6000-0001`, correo `…@tommalo.example`, dominio `tommalo.example`,
   productos genéricos marcados de prueba («Crema de prueba», «Lámpara de prueba»), categorías Belleza / Hogar /
   Salud / Otros (xmlids `website_dcasa.public_category_belleza|hogar|salud|otro` y
   `dcasa_catalogo.product_category_belleza|hogar|salud|otro`). Las categorías de muebles ya no existen.
3. Las pruebas que dicen «no hay datos de otro negocio» se conservan; sus listas pueden llevar nombres de marca
   (D'CASA, Baby Caleb, dcasapty) pero **nunca** teléfonos, RUC ni direcciones reales.
4. **No se saltan ni se borran pruebas para que pasen**: se ajusta su contenido. Solo se borra una prueba que
   comprobaba contenido exclusivo de otro negocio (y se dice en el informe).
5. El prefijo `dcasa_` (módulos, campos, variables `DCASA_*`) se queda.
6. Marca provisional neutra: Tommalo no ha decidido logo ni colores. Los valores de marca van centralizados
   (variables SCSS de `primary_variables.scss`, `res_company_data.xml`, `website_data.xml`) con palabras `PENDIENTE`
   en el comentario. Paleta provisional: blanco, grises y un acento oscuro, que pasen los contrastes. Sin logo: no
   se inventa uno (texto «Tommalo» como marca de palabra con la tipografía del sistema/Inter).
7. Páginas de marketing de Baby Caleb (/beneficios, /historia, /tips, /como-comprar, /faq y sus secciones,
   testimonios, sellos, educación) se quitan por completo (vistas, rutas, menú, pie, tests, imágenes). Tommalo las
   escribe cuando decida su mensaje.
8. Referencias visuales (`tests/referencia/*.webp`): si el cambio de contenido las hace diferir, se regeneran con los
   scripts `scripts/actualizar_referencias_visuales*.sh` (o a mano con Chromium en `/opt/pw-browsers/chromium`) y se
   dice en el informe: no se pudo comprobar contra el CI.
9. No hagas `git commit` ni `git push`: la sesión principal lo hace. No toques carpetas que no son tuyas.

## Cómo correr pruebas de Odoo aquí
Postgres 16 ya corre (rol `odoo`/`odoo`). Odoo está en `/tmp/odoo19`, el venv en `/tmp/venv`. Una instancia por agente
(nombre de base y puerto propios):

```bash
cd /home/user/Tommalo_New_word
PYTHON=/tmp/venv/bin/python ODOO_DIR=/tmp/odoo19 PATH=/tmp/venv/bin:$PATH \
  DB_NAME=t_<tunombre> HTTP_PORT=<puerto propio> LOG=/tmp/t_<tunombre>.log \
  scripts/test.sh modulo1,modulo2
```
`scripts/test.sh` falla con cualquier `ERROR` en el registro. Las pruebas de navegador usan Chromium
(`ln -s /opt/pw-browsers/chromium /tmp/venv/bin/chromium` si hace falta). `ruff check addons` (ya instalado).
