{
    'name': "Tommalo — Sitio web",
    'summary': "Sitio web y tienda con la marca de Tommalo, mantenido desde el código (sin constructor)",
    'description': """
Sitio web sobre el constructor de sitios y el eCommerce de Odoo (base de Tommalo, copiada de la plantilla de origen y
dejada genérica):

* Marca provisional neutra: blanco, grises y un acento oscuro (PENDIENTE: colores de Tommalo), cargados como paleta del
  sitio (static/src/scss/primary_variables.scss): se pueden ajustar desde el editor sin tocar código.
* Portada simple: hero de texto (titular y subtítulo PENDIENTE, editables), carrusel de productos de la tienda con
  precio y «Agregar» en un clic, cobertura y contacto, y la banda final «Ver el catálogo».
* Ficha de producto con WhatsApp del producto y botón fijo en el celular; tienda a 4 columnas; datos estructurados.
* Pie de página sin datos inventados y botón flotante de WhatsApp, sin el crédito de Odoo.
* Animaciones de entrada (secciones y titulares) y opiniones de Google en una cinta en movimiento (data/resenas.json,
  hoy vacío: sin opiniones no sale).
* Fotos de producto en WebP (y JPEG de respaldo) al ancho justo: ``/dcasa/img/...``, generadas una vez y cacheadas un
  año en el borde (models/imagen.py).
* Enlaces al programa Socios (/socios): puntos, referidos y premios.
* Búsqueda: la lupa a la vista en el celular; la caja de la cabecera busca en el catálogo (/shop?search=…) y una
  tilde ya no da «no coincidió…»; sin resultados ofrece las categorías (Belleza, Hogar, Salud y Otros) y WhatsApp.
* Contacto, horario y opiniones de productos de quien los compró y pagó, publicadas solo si Gerencia las aprueba.
* Campaña del sitio (Black Weekend, Black Friday…): banda en la portada, página /promociones y etiqueta en las
  tarjetas de los productos marcados, solo dentro de la ventana de la campaña (models/black_weekend.py).
* Carrusel del hero con productos propios que Gerencia elige y ordena en Sitio web › Carrusel de la portada (vacío =
  hero de solo texto) (models/portada.py).
* Páginas legales (privacidad y términos): texto provisional que revisa la asesoría legal de Tommalo.

Todo el contenido de las páginas es editable con el constructor de Odoo
(Sitio web > Editar), sin programador.
""",
    'version': '19.0.1.20.0',
    'category': 'Website/Website',
    'author': "Tommalo",
    'website': 'https://tommalo.example',
    'license': 'LGPL-3',
    'depends': ['dcasa_base', 'dcasa_socios', 'dcasa_contactos', 'website_sale'],
    'data': [
        'security/dcasa_roles_website.xml',
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'data/product_public_category_data.xml',
        'views/res_config_settings_views.xml',
        'views/apartados_views.xml',
        'views/resenas_views.xml',
        'views/layout_templates.xml',
        'views/cabecera_templates.xml',
        'views/accesibilidad_templates.xml',
        'views/resenas_templates.xml',
        'views/black_weekend_templates.xml',
        'views/campana_views.xml',
        'views/portada_views.xml',
        'views/homepage_templates.xml',
        'views/paginas_tommalo_templates.xml',
        'views/paginas_templates.xml',
        'views/legal_templates.xml',
        'data/website_menu_data.xml',
        'data/tienda_data.xml',
        'views/tienda_templates.xml',
        'views/opiniones_templates.xml',
        'views/buscador_templates.xml',
        'views/nombres_cliente_templates.xml',
        'views/pago_templates.xml',
        'data/seo_data.xml',
        'data/black_weekend_data.xml',
        'data/ir_cron_data.xml',
        'data/portada_data.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'website_dcasa/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'website_dcasa/static/src/scss/fuentes.scss',
            'website_dcasa/static/src/scss/dcasa.scss',
            'website_dcasa/static/src/scss/pago.scss',
            'website_dcasa/static/src/js/animaciones.js',
            'website_dcasa/static/src/js/carrito.js',
            'website_dcasa/static/src/js/carril.js',
            'website_dcasa/static/src/js/foto_grande.js',
            'website_dcasa/static/src/js/mapa.js',
            'website_dcasa/static/src/js/portada.js',
        ],
    },
    'installable': True,
}
