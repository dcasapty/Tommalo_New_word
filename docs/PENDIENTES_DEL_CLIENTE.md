# Lo que falta que decida Tommalo

Escrito en palabras sencillas. Cada punto dice **qué se necesita**, **por qué importa** y **qué recomendamos**. Mientras no
haya respuesta, la base queda con un valor seguro (o vacío) y nada se inventa. Las preguntas más importantes van primero.

## 1. ¿Tommalo es el proveedor, o compra a otro proveedor?
- **Por qué importa:** en Dropi aparece un «costo proveedor». Si Tommalo es el mismo proveedor, ese costo no es su costo
  real, y las ganancias y los reportes saldrían mal.
- **Recomendamos:** que el cliente diga cuál es su costo real de cada producto (o un porcentaje). Hasta entonces el
  costo queda vacío en el sistema.

## 2. ¿El precio al público es el «precio sugerido» de Dropi?
- **Por qué importa:** el catálogo trae precio sugerido de 8 a 94 USD. Si no es el que se va a cobrar, hay que decir cuál.
- **Recomendamos:** usar el sugerido solo como punto de partida y que el cliente revise los productos más vendidos.

## 3. ¿Tommalo cobra ITBMS (el impuesto del 7 %)?
- **Por qué importa:** cambia todos los precios que ve el cliente y las facturas.
- **Hoy:** la base cobra el 7 % (`DCASA_COBRA_ITBMS=1` en `docker/negocio.env`).
- **Recomendamos:** confirmarlo con quien lleve la contabilidad antes de abrir al público.

## 4. ¿Tommalo tiene tienda física?
- **Por qué importa:** si tiene, el cliente puede «retirar en tienda» y «pagar en la tienda» (y hace falta la dirección y el
  horario). Si no, esas opciones se esconden.
- **Hoy:** sin tienda física (`DCASA_TIENDA_FISICA=0`).
- **Recomendamos:** dejarlo en «sin tienda» si todo se vende por internet y se envía desde bodega.

## 5. ¿Desde dónde despacha Tommalo y en qué vehículo?
- **Por qué importa:** el sistema calcula el costo del envío desde un «punto de salida». Hace falta el lugar de salida y si
  los envíos van en moto, carro, o con o sin corredores (mensajeros por zona).
- **Hoy:** el punto de salida y las tarifas están **vacíos** (no se copian los de otros negocios).
- **Recomendamos:** que el cliente diga dónde está su bodega y quién reparte; con eso se arman las zonas y la tarifa, que
  la aprueba Gerencia.

## 6. Logo y colores
- **Qué se necesita:** el logo (imagen con fondo transparente) y los colores de la marca. No hay archivo de logo (las fotos
  antiguas llevan la marca «TOMMALO.CO», que no sirve de logo).
- **Hoy:** una «T» gris como marcador y colores neutros ([MARCA_TOMMALO.md](MARCA_TOMMALO.md)).
- **Recomendamos:** enviar el logo en PNG y dos colores (uno oscuro para letras y uno de acento).

## 7. ¿El repositorio se queda público o pasa a privado?
- **Por qué importa:** hoy cualquiera puede ver el código en GitHub. **El catálogo con costos, contactos y claves no se
  sube hasta decidir esto.** En privado, los «Environments» de GitHub (donde viven las claves) cuestan un plan de pago.
- **Recomendamos:** privado antes de subir el catálogo real, y pagar el plan de GitHub que haga falta.

## 8. Dominio propio
- **Qué se necesita:** el nombre del dominio (por ejemplo `tommalo.…`) y que esté en la cuenta de Cloudflare del cliente.
- **Hoy:** sin dominio; el sitio respondería en una dirección `workers.dev` ([DOMINIO.md](DOMINIO.md)).

## 9. Qué inteligencia artificial usar para los asistentes
- **Por qué importa:** unos modelos guardan las conversaciones para entrenarse; la política de privacidad lo tiene que
  decir. También cuesta dinero por uso.
- **Hoy:** sin proveedor elegido y sin claves.
- **Recomendamos:** elegir uno que **no** entrene con las conversaciones y poner un tope de gasto mensual.

## 10. Datos de la empresa
- **Qué se necesita:** RUC y dígito verificador, razón social, dirección, teléfono, correo y WhatsApp de atención, redes y horario.
- **Hoy:** todo vacío o `PENDIENTE` (se escribe en *Ajustes › Empresas*, no en el repositorio).

## 11. Textos legales y del sitio
- **Qué se necesita:** política de privacidad, términos, garantía y cambios, revisados por su asesoría legal; y el mensaje
  de la portada (titular, beneficios, preguntas frecuentes).
- **Hoy:** textos provisionales marcados «PENDIENTE», sin plazos ni promesas.

## 12. Catálogo
- **Qué se necesita:** la decisión de la pregunta 7 y luego dar el «sí» para subirlo.
- **Estado:** 183 productos, 598 variantes, 13 428 unidades y 992 imágenes ya preparados en la computadora del cliente
  (módulo `dcasa_catalogo_tommalo`). 40 productos están incompletos y 70 descripciones traen correos que hay que quitar.
  No se sube todavía.

## 13. Programas de puntos y de vendedores
- **Qué se necesita:** si Tommalo quiere programa de puntos («Socios») o de vendedores, y sus cifras.
- **Hoy:** apagados, todas las cifras en `PENDIENTE`.

## 14. Financieras y formas de pago
- **Qué se necesita:** qué formas de pago ofrece (Yappy, tarjeta, transferencia, efectivo).
- **Hoy:** el sistema trae de la plantilla las formas «Efectivo», «Yappy» y «Tarjeta» y dos financieras (Tafi y Crediviva)
  de otro negocio. **Recomendamos quitar las financieras** si Tommalo no las usa (se archivan en Odoo).

## 15. Tamaño de la caja del servidor
- **Hoy:** `standard-1` (la de la plantilla, unos 28-31 USD al mes si está encendida siempre). Se cambia con una línea.
- **Recomendamos:** empezar así y revisar la factura el primer mes.
