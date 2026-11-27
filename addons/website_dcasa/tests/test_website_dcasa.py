import base64
import json
import re

from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools.misc import file_open


@tagged('post_install', '-at_install')
class TestWhatsappLink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.website = self.env.ref('website.default_website')

    def test_whatsapp_url_uses_configured_number(self):
        self.website.dcasa_whatsapp_number = '+507 6000-0002'
        url = self.website._dcasa_whatsapp_url('Hola Tommalo')
        self.assertTrue(url.startswith('https://api.whatsapp.com/send?phone=50760000002&text='))
        self.assertIn('Hola%20Tommalo', url)

    def test_whatsapp_de_fabrica_esta_vacio(self):
        """El sitio nace con el nombre «Tommalo» y SIN WhatsApp ni redes (PENDIENTE: no se inventan); el saludo ya dice
        «Tommalo». Sin número, el enlace va a /contactus."""
        self.assertFalse(self.website.dcasa_whatsapp_number)
        self.assertEqual(self.website.name, 'Tommalo')
        self.assertFalse(self.website.social_instagram)
        self.assertFalse(self.website.social_tiktok)
        self.assertFalse(self.website.social_facebook)
        self.assertEqual(self.website._dcasa_whatsapp_url(), '/contactus')
        self.website.dcasa_whatsapp_number = '+507 6000-0002'
        self.assertIn('Hola%20Tommalo', self.website._dcasa_whatsapp_url())

    def test_whatsapp_url_falls_back_to_company_phone(self):
        self.website.dcasa_whatsapp_number = False
        self.website.company_id.phone = '+507 6000-0001'
        self.assertTrue(self.website._dcasa_whatsapp_url().startswith('https://api.whatsapp.com/send?phone=50760000001&'))

    def test_whatsapp_url_without_number_goes_to_contact(self):
        self.website.dcasa_whatsapp_number = False
        self.website.company_id.phone = False
        self.assertEqual(self.website._dcasa_whatsapp_url(), '/contactus')


@tagged('post_install', '-at_install')
class TestWebsitePages(HttpCase):

    def setUp(self):
        super().setUp()
        self.env.ref('website.default_website').dcasa_whatsapp_number = '+507 6000-0002'
        self.env.company.email = 'ventas@tommalo.example'

    def test_homepage(self):
        # Con «Brian de la tienda» (dcasa_brian_tienda) encendido, la burbuja flotante es la suya: aquí se prueba la de
        # WhatsApp, la que sale con Brian apagado o sin ese módulo.
        self.env['ir.config_parameter'].sudo().set_param('dcasa_brian_tienda.activo', 'False')
        response = self.url_open('/')
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn('PENDIENTE: titular de la portada', html)
        self.assertIn('https://api.whatsapp.com/send?phone=50760000002', html)
        self.assertIn('o_dcasa_wa_float', html)
        self.assertIn('ventas@tommalo.example', html, 'La cobertura y el contacto muestran los datos de la empresa')
        for de_la_tienda_de_origen in ("D'CASA", 'D&#39;CASA', 'dcasapty', 'La Chorrera',
                                       'Baby Caleb', 'Nateen', 'bebé', 'pañal'):
            self.assertNotIn(de_la_tienda_de_origen, html)
        self.assertNotIn('555-555-5556', html, 'No debe quedar el teléfono de ejemplo de Odoo')
        self.assertNotIn('Company name', html, 'No debe quedar el copyright de ejemplo de Odoo')

    def test_socios_linked_from_site(self):
        home = self.url_open('/').text
        self.assertIn('href="/socios"', home, 'Socios sigue en el pie')
        # La banda solo sale con las cifras del programa puestas (hoy todas en PENDIENTE): no promete puntos.
        self.assertNotIn('Suma puntos y gana invitando', home)
        response = self.url_open('/socios')
        self.assertEqual(response.status_code, 200)
        # El mismo sitio y el mismo pie (con su WhatsApp). El botón flotante de WhatsApp no sirve de prueba: con
        # Brian de la tienda encendido, la burbuja es la del chat.
        self.assertIn('o_dcasa_pie_nombre', response.text, 'La app del socio usa el mismo sitio y pie')
        self.assertIn('href="/whatsapp"', response.text)

    def test_terminos_de_odoo_llevan_a_los_reales(self):
        """La factura y el portal enlazan /terms: la plantilla de Odoo trae términos inventados en inglés."""
        self.env['ir.config_parameter'].sudo().set_param('account.use_invoice_terms', True)
        self.env.company.terms_type = 'html'
        respuesta = self.url_open('/terms', allow_redirects=False)
        self.assertEqual(respuesta.status_code, 301)
        self.assertTrue(respuesta.headers['Location'].endswith('/terminos'))
        self.assertNotIn('Odoo S.A.', self.url_open('/terms').text)

    def test_shop(self):
        self.assertEqual(self.url_open('/shop').status_code, 200)

    def test_frontend_css_compiles_with_brand(self):
        """La hoja del sitio compila con la marca provisional neutra (blanco, grises y un acento oscuro) y ya no queda
        nada de los colores ni de la letra de las tiendas de origen."""
        html = self.url_open('/').text
        css_links = re.findall(r'href="([^"]*web\.assets_frontend[^"]*\.css)"', html)
        self.assertTrue(css_links, 'La página debe enlazar el bundle CSS del sitio')
        css = self.url_open(css_links[0]).text
        self.assertIn('o_dcasa_pcard', css)
        self.assertIn('o_dcasa_hero_texto', css)
        self.assertIn('o_dcasa_wa_float', css)
        bajo = css.lower()
        for color in ('#fafafa', '#ffffff', '#262626', '#d4d4d4', '#bdbdbd', '#595959'):
            self.assertIn(color, bajo, f'falta el {color} de la paleta neutra')
        # La paleta del sitio (de la que Odoo saca los botones, los enlaces y las combinaciones de color).
        self.assertRegex(bajo, r'--o-color-1:\s*#d4d4d4')
        self.assertRegex(bajo, r'--o-color-5:\s*#262626')
        # Y en las hojas de este módulo no queda ningún color de marca de otro negocio, ni su letra.
        for hoja in ('primary_variables.scss', 'fuentes.scss', 'dcasa.scss', 'pago.scss'):
            with file_open(f'website_dcasa/static/src/scss/{hoja}') as archivo:
                fuente = archivo.read().lower()
            for de_otro in ('#1340b1', '#fed00f', '#0e2a6b', '#0f3591', '#ee924a', '#91c9a2', '#1b3246', '#f9f6ed',
                            '#53735c', "'anton'", "'oswald'"):
                self.assertNotIn(de_otro, fuente, f'{hoja}: quedó {de_otro} de otra marca')


@tagged('post_install', '-at_install')
class TestPortadaDinamica(HttpCase):
    """Carriles de productos, compra en 1 clic y SEO de la portada."""

    def setUp(self):
        super().setUp()
        self.website = self.env.ref('website.default_website')
        self.website.dcasa_whatsapp_number = '+507 6000-0002'
        self.belleza = self.env.ref('website_dcasa.public_category_belleza')
        self.hogar = self.env.ref('website_dcasa.public_category_hogar')
        Product = self.env['product.template']
        self.crema = Product.create({
            'name': 'CREMA DE PRUEBA', 'list_price': 123.45, 'is_published': True,
            'taxes_id': [(5, 0, 0)],  # sin impuesto: la cifra mostrada es la del precio
            'website_sequence': -100, 'public_categ_ids': [(6, 0, self.belleza.ids)],
        })
        self.lampara = Product.create({
            'name': 'LÁMPARA DE PRUEBA', 'list_price': 99.0, 'is_published': True,
            'website_sequence': -99, 'public_categ_ids': [(6, 0, self.hogar.ids)],
        })
        self.oculto = Product.create({
            'name': 'PRODUCTO SIN PUBLICAR', 'list_price': 10.0, 'is_published': False,
            'website_sequence': -101,
        })

    def test_productos_de_la_portada(self):
        todos = [i['producto'] for i in self.website._dcasa_productos(limit=50)]
        self.assertIn(self.crema, todos)
        self.assertNotIn(self.oculto, todos, 'La portada solo muestra lo publicado')
        del_hogar = [i['producto'] for i in self.website._dcasa_productos(limit=50, categorias=['hogar'])]
        self.assertIn(self.lampara, del_hogar)
        self.assertNotIn(self.crema, del_hogar)

    def test_una_categoria_sin_nada_publicado_abre_whatsapp_y_vuelve_sola_al_publicar(self):
        """Una categoría sin nada publicado no lleva a una página de error: la tarjeta abre WhatsApp; con algo
        publicado, su página de la tienda. (La portada no enseña las categorías; las ofrece la búsqueda sin resultados:
        TestBuscador.)"""
        self.website.dcasa_whatsapp_number = '+507 6000-0002'

        def tarjeta(nombre):
            return next(t for t in self.website._dcasa_categorias() if t['nombre'] == nombre)

        self.assertEqual([t['nombre'] for t in self.website._dcasa_categorias()],
                         ['Belleza', 'Hogar', 'Salud', 'Otros'])
        con = tarjeta('Hogar')
        self.assertFalse(con['whatsapp'])
        self.assertTrue(con['url'].startswith('/shop/category/'), con['url'])
        # Todo lo publicado en Hogar, no solo el de esta prueba.
        publicados = self.env['product.template'].sudo().search([
            ('public_categ_ids', 'child_of', self.hogar.id), ('is_published', '=', True)])
        self.assertIn(self.lampara, publicados)
        publicados.is_published = False
        sin = tarjeta('Hogar')
        self.assertTrue(sin['whatsapp'])
        self.assertTrue(sin['url'].startswith('https://api.whatsapp.com/send?phone=50760000002&text='), sin['url'])
        self.assertIn('hogar', sin['url'])
        self.assertFalse(tarjeta('Belleza')['whatsapp'], 'las que tienen productos siguen a su página')
        self.assertNotIn('imagen', tarjeta('Belleza'))
        self.lampara.is_published = True
        self.assertFalse(tarjeta('Hogar')['whatsapp'], 'al publicar, vuelve sola a la tienda')

    def test_la_portada_no_trae_nada_de_otros_negocios(self):
        """Ni fotos ni textos de las tiendas de origen (muebles, bebés), aunque haya algo publicado."""
        self.crema.is_published = True
        portada = self.url_open('/').text
        for de_otro in ('dcasa-cat-titulo', 'Compra por espacio', 'Para dormir mejor', 'o_dcasa_cine',
                        'o_dcasa_categorias', 'o_dcasa_galeria', 'img/cat-', 'img/insp-', 'img/split-',
                        'img/hero', 'Nateen', 'bebé', 'Pañal', 'o_dcasa_testimonio', 'o_dcasa_confianza',
                        'o_dcasa_educacion', 'o_dcasa_hero_tarjeta', 'o_dcasa_hero_media'):
            self.assertNotIn(de_otro, portada)
        for archivo in ('cat-salas.webp', 'hero.webp', 'hero-bebe-800.webp', 'hero-bebe-1200.webp', 'insp-3.webp',
                        'promo-nateen-800.webp', 'sello-badge-224.webp', 'tip-cloro-720.webp',
                        'panal-nateen-tarjeta.webp'):
            self.assertEqual(self.url_open(f'/website_dcasa/static/src/img/{archivo}').status_code, 404,
                             f'{archivo} (de otro negocio) ya no está en el módulo')

    def test_la_portada_simple_y_neutra(self):
        """Hero de texto (PENDIENTE, sin foto), productos de la tienda, cobertura y contacto, y la banda final."""
        portada = self.url_open('/').text
        piezas = [
            'PENDIENTE: titular de la portada',      # 1. hero
            'Lo más buscado',                        # 2. productos
            'Vendemos en línea y te lo llevamos.',   # 3. cobertura
            'Explora el catálogo de Tommalo.',       # 4. banda final
        ]
        posiciones = [portada.index(pieza) for pieza in piezas]
        self.assertEqual(posiciones, sorted(posiciones), 'las secciones en su orden')
        self.assertNotIn('<img src="/website_dcasa/static/src/img/hero', portada, 'sin foto de hero')
        self.assertNotIn('o_dcasa_preguntas', portada)
        self.assertNotIn('o_dcasa_socios_band', portada, 'sin la banda de Socios: sus cifras siguen en PENDIENTE')
        # «Cómo pedir» no promete lo que este sistema no hace: el pago y el envío se coordinan por WhatsApp.
        como_pedir = re.search(r'Cómo pedir</h3>\s*<p>(.*?)</p>', portada, re.S).group(1)
        self.assertIn('WhatsApp para coordinar el pago', ' '.join(como_pedir.split()))
        self.assertNotIn('en la misma página', como_pedir)
        self.assertIn('PENDIENTE (lo decide Tommalo)', portada, 'las zonas de entrega dicen PENDIENTE')
        for de_dcasa in ("D'CASA", 'D&#39;CASA', 'dcasapty', '60000001'):
            self.assertNotIn(de_dcasa, portada)

    def test_portada_muestra_productos_con_precio_y_agregar(self):
        html = self.url_open('/').text
        self.assertIn('Crema de Prueba', html)
        self.assertRegex(html, r'123[.,]45')
        self.assertIn('action="/dcasa/carrito/agregar"', html)
        self.assertNotIn('PRODUCTO SIN PUBLICAR', html)
        self.assertIn('Lo más buscado', html)

    def test_cifras_de_socios_salen_de_puntos_json(self):
        # Cifras de PRUEBA encima de puntos.json (dcasa_socios/tests/common.py): la banda las lee de ahí.
        from odoo.addons.dcasa_socios.tests.common import parche_de_reglas_de_prueba  # noqa: PLC0415
        with parche_de_reglas_de_prueba():
            reglas = self.website._dcasa_reglas_socios()
            html = self.url_open('/').text
        self.assertIn('{:,}'.format(reglas['referido']['puntosAlPadrino']), html)
        self.assertIn('{:,}'.format(reglas['referido']['puntosAlAhijado']), html)

    def test_con_puntos_json_de_fabrica_la_banda_no_dice_cifras(self):
        """Todo en PENDIENTE (2026-11-18): la banda de Socios no enseña ninguna cifra."""
        html = self.url_open('/').text
        banda = re.search(r'<section class="o_dcasa_socios_band".*?</section>', html, re.S)
        texto = re.sub(r'<[^>]+>', ' ', banda.group(0)) if banda else ''
        self.assertNotRegex(texto, r'\d', 'ninguna cifra en la banda')
        self.assertNotIn('por cada dólar', texto)

    def test_json_ld_tienda(self):
        self.env.company.write({'phone': '+507 6000-0001', 'email': 'ventas@tommalo.example'})
        html = self.url_open('/').text
        bloques = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
        datos = next((b for b in bloques if b.get('@type') == 'OnlineStore'), None)
        self.assertTrue(datos, 'La portada publica los datos de la tienda (en línea: Tommalo no tiene local)')
        self.assertEqual(datos['name'], 'Tommalo')
        self.assertEqual(datos['telephone'], '+507 6000-0001')
        self.assertEqual(datos['email'], 'ventas@tommalo.example')
        self.assertEqual(datos['address'], {'@type': 'PostalAddress', 'addressCountry': 'PA'},
                         'Solo lo que la empresa tiene escrito: sin calle, ciudad ni provincia inventadas')
        self.assertNotIn('sameAs', datos, 'sin redes escritas, sin enlaces')
        for sin_local in ('geo', 'hasMap', 'image'):
            self.assertNotIn(sin_local, datos)
        self.assertNotIn('FurnitureStore', html)
        self.assertNotIn('OnlineStore', self.url_open('/shop').text, 'Solo en la portada')

    def test_seo_de_la_portada(self):
        html = self.url_open('/').text
        self.assertIn('Tommalo Panamá | Tienda en línea', html)
        self.assertIn('Tommalo: tienda en línea de belleza, hogar y salud', html)
        self.assertIn('name="description"', html)

    def test_agregar_al_carrito_en_un_clic(self):
        self.authenticate(None, None)
        home = self.url_open('/').text
        token = re.search(r'name="csrf_token" value=[\'"]([^\'"]+)', home).group(1)
        respuesta = self.url_open('/dcasa/carrito/agregar', data={
            'csrf_token': token, 'product_template_id': self.crema.id,
        }, allow_redirects=False)
        self.assertIn(respuesta.status_code, (302, 303))
        self.assertTrue(respuesta.headers['Location'].endswith('/shop/cart'))
        carrito = self.url_open('/shop/cart').text
        self.assertIn('Crema de Prueba', carrito)

    def test_agregar_producto_no_publicado_no_entra(self):
        self.authenticate(None, None)
        home = self.url_open('/').text
        token = re.search(r'name="csrf_token" value=[\'"]([^\'"]+)', home).group(1)
        respuesta = self.url_open('/dcasa/carrito/agregar', data={
            'csrf_token': token, 'product_template_id': self.oculto.id,
        }, allow_redirects=False)
        self.assertTrue(respuesta.headers['Location'].endswith('/shop'))
        self.assertNotIn('PRODUCTO SIN PUBLICAR', self.url_open('/shop/cart').text)

    def test_ficha_de_producto_con_whatsapp_y_sellos(self):
        html = self.url_open(self.crema.website_url).text
        self.assertIn('o_dcasa_sellos', html)
        # Formato título (F5).
        self.assertIn('Hola%20Tommalo%2C%20me%20interesa%3A%20Crema%20de%20Prueba', html)
        self.assertIn('Entrega a domicilio.', html)
        self.assertIn('Te ayudamos por WhatsApp a elegir tu producto', html)
        for sin_tienda in ('Míralo en tienda', 'Te lo llevas hoy', 'este mueble', 'talla'):
            self.assertNotIn(sin_tienda, html)

    def test_ficha_sin_promesas_inventadas(self):
        html = self.url_open(self.crema.website_url).text
        self.assertNotIn('30-day', html)
        self.assertNotIn('30 días', html)

    def test_tienda_con_descripcion_para_google(self):
        html = self.url_open('/shop').text
        self.assertIn('<meta name="description" content="Catálogo de Tommalo: belleza, hogar y salud', html)

    def _token(self):
        self.authenticate(None, None)
        home = self.url_open('/').text
        return re.search(r'name="csrf_token" value=[\'"]([^\'"]+)', home).group(1)

    def _agregar(self, product_template_id, token=None):
        return self.url_open('/dcasa/carrito/agregar', data={
            'csrf_token': token or self._token(), 'product_template_id': product_template_id,
        }, allow_redirects=False)

    def test_agregar_sin_csrf_se_rechaza(self):
        self.authenticate(None, None)
        respuesta = self.url_open('/dcasa/carrito/agregar', data={'product_template_id': self.crema.id},
                                  allow_redirects=False)
        self.assertEqual(respuesta.status_code, 400)

    def test_agregar_id_invalido_va_a_la_tienda(self):
        respuesta = self._agregar('abc')
        self.assertTrue(respuesta.headers['Location'].endswith('/shop'))

    def test_producto_con_variantes_va_a_la_ficha(self):
        color = self.env['product.attribute'].create({
            'name': 'Color prueba',
            'value_ids': [(0, 0, {'name': 'Gris'}), (0, 0, {'name': 'Azul'})],
        })
        self.crema.attribute_line_ids = [(0, 0, {
            'attribute_id': color.id, 'value_ids': [(6, 0, color.value_ids.ids)],
        })]
        respuesta = self._agregar(self.crema.id)
        self.assertIn(self.crema.website_url, respuesta.headers['Location'])
        # v3 (2026-11-15): el mismo ícono del carrito, que lleva a la ficha y lo dice a los lectores de pantalla.
        self.assertIn('Elegir opciones de', self.url_open('/').text, 'Con variantes la tarjeta lleva a la ficha')

    def test_precio_cero_bloqueado_no_se_agrega(self):
        self.website.prevent_zero_price_sale = True
        gratis = self.env['product.template'].create({
            'name': 'PRODUCTO A CONSULTAR', 'list_price': 0.0, 'is_published': True, 'website_sequence': -102,
        })
        respuesta = self._agregar(gratis.id)
        self.assertIn(gratis.website_url, respuesta.headers['Location'])
        self.assertNotIn('PRODUCTO A CONSULTAR', self.url_open('/shop/cart').text)

    def test_whatsapp_redirige_al_numero_configurado(self):
        self.website.dcasa_whatsapp_number = '+507 6000-0002'
        respuesta = self.url_open('/whatsapp?texto=Hola', allow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.headers['Location'].startswith(
            'https://api.whatsapp.com/send?phone=50760000002&text=Hola'))
        self.website.dcasa_whatsapp_number = False
        self.website.company_id.phone = False
        respuesta = self.url_open('/whatsapp', allow_redirects=False)
        self.assertTrue(respuesta.headers['Location'].endswith('/contactus'))

    def test_json_ld_no_cierra_el_script(self):
        self.website.company_id.name = 'Tommalo </script><script>alert(1)</script>'
        texto = str(self.website._dcasa_json_ld().__html__())  # lo que QWeb imprime en <script>
        self.assertNotIn('<', texto)
        self.assertEqual(json.loads(texto)['name'], self.website.company_id.name)
        self.assertNotIn('priceRange', texto, 'Sin cifras inventadas')


@tagged('post_install', '-at_install')
class TestMarcaYMovimiento(HttpCase):
    """Sin marca de Odoo, hero sin placa, reseñas reales y animaciones."""

    def test_sin_credito_de_odoo(self):
        for ruta in ('/', '/shop', '/socios'):
            html = self.url_open(ruta).text
            self.assertNotIn('o_brand_promotion', html, ruta)
            self.assertNotIn('utm_source=db', html, ruta)
            self.assertNotIn('Con la tecnología de', html, ruta)

    def test_favicon_del_sitio(self):
        website = self.env.ref('website.default_website')
        # Odoo lo guarda convertido a .ico: basta con que ya no sea el de Odoo.
        with file_open('web/static/img/favicon.ico', 'rb') as archivo:
            self.assertNotEqual(base64.b64decode(website.favicon), archivo.read())
        self.assertTrue(website.favicon)

    def test_hero_y_cabeceras_de_pagina_sin_foto(self):
        """El hero de texto, con el antetítulo en píldora; las páginas interiores, la misma cabecera, sin foto."""
        html = self.url_open('/').text
        self.assertIn('o_dcasa_hero_texto', html)
        self.assertIn('o_dcasa_kicker_pildora', html)
        self.assertNotIn('o_dcasa_placa', html)
        self.assertNotIn('o_dcasa_kicker_light', html)
        for ruta in ('/socios', '/privacidad', '/web/login', '/visitanos', '/contactus'):
            pagina = self.url_open(ruta).text
            cabecera = re.search(r'<section class="o_dcasa_hero o_dcasa_hero_compacto[^"]*".*?</section>', pagina, re.S)
            self.assertTrue(cabecera, f'{ruta}: la cabecera de página de siempre')
            self.assertNotIn('<img', cabecera.group(0), f'{ruta}: la cabecera ya no lleva foto')
            self.assertIn('o_dcasa_kicker_pildora', cabecera.group(0))

    def test_sin_resenas_de_otra_empresa(self):
        """Todavía no hay ficha de Google de Tommalo en data/resenas.json. Sin opiniones, la cinta de la portada no sale
        (y no se inventa ninguna)."""
        resenas = self.env.ref('website.default_website')._dcasa_resenas()
        self.assertEqual(resenas['opiniones'], [])
        html = self.url_open('/').text
        self.assertNotIn('Déjanos tu opinión en Google', html)
        self.assertNotIn('o_dcasa_resenas_pausa', html)

    def test_resenas_reales_de_google(self):
        """Con la copia de las reseñas de la ficha de Google (la que pegue Tommalo en data/resenas.json), la cinta."""
        from odoo.addons.website_dcasa.models import website as modulo
        original = modulo._leer_resenas
        modulo._leer_resenas = lambda: {
            'ficha': 'https://share.google/ficha-de-prueba', 'puntuacion': 5.0, 'total': 4,
            'opiniones': [{'autor': f'Clienta {n}', 'estrellas': 5, 'cuando': 'Hace un mes', 'texto': 'Muy bien.'}
                          for n in range(1, 5)]}
        self.addCleanup(setattr, modulo, '_leer_resenas', original)
        resenas = self.env.ref('website.default_website')._dcasa_resenas()
        html = self.url_open('/').text
        self.assertIn(resenas['ficha'], html)
        self.assertIn('Déjanos tu opinión en Google', html)
        self.assertIn('o_dcasa_resenas_pausa', html, 'La cinta se puede pausar (WCAG 2.2.2)')
        for opinion in resenas['opiniones']:
            self.assertIn(opinion['autor'], html)
        self.assertGreater(resenas['copias'], 1)
        self.assertEqual(resenas['copias'] % 2, 0, 'El bucle sin salto necesita un número par de copias')
        self.assertGreaterEqual(len(resenas['opiniones']) * resenas['copias'] / 2, 8)

    def test_animaciones_cargan(self):
        html = self.url_open('/').text
        self.assertIn('data-anim-entrada', html)
        self.assertIn('data-titular', html)
        scripts = re.findall(r'src="([^"]*web\.assets_frontend[^"]*\.js)"', html)
        self.assertTrue(scripts)
        js = ''.join(self.url_open(src).text for src in scripts)
        self.assertIn('website_dcasa.revelar', js, 'Las animaciones son Interactions de Odoo')

    def test_menu_de_tommalo(self):
        """El menú de la base: solo el catálogo; las páginas de marketing las agrega Tommalo cuando las escriba."""
        website = self.env.ref('website.default_website')
        menu = website.menu_id.child_id.sorted('sequence')
        self.assertEqual(menu.mapped('name'), ['Productos'])
        self.assertEqual(menu.mapped('url'), ['/shop'])
        tienda = menu.filtered(lambda m: m.url == '/shop')
        self.assertEqual(tienda.with_context(lang='es_419').name, 'Productos', 'No «Tienda» en español')
        for url in ('/socios', '/visitanos', '/beneficios', '/historia', '/tips', '/como-comprar', '/faq'):
            self.assertFalse(menu.filtered(lambda m, url=url: m.url == url), f'{url} no va en el menú')

    def test_paginas_de_marketing_ya_no_existen(self):
        for ruta in ('/beneficios', '/historia', '/tips', '/como-comprar', '/faq'):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.url_open(ruta).status_code, 404)

    def test_menu_se_arma_otra_vez_sin_duplicar(self):
        """La migración de 19.0.1.20.0 lo vuelve a armar en staging: el menú viejo (Socios · Contacto) pasa al actual y
        correrlo dos veces no duplica nada."""
        website = self.env.ref('website.default_website')
        Menu = self.env['website.menu']
        for nombre, url in (('Socios Tommalo', '/socios'), ('Contacto', '/visitanos')):
            Menu.create({'name': nombre, 'url': url, 'parent_id': website.menu_id.id, 'website_id': website.id})
        self.env['website']._dcasa_armar_menu_principal()
        self.env['website']._dcasa_armar_menu_principal()
        self.assertEqual(website.menu_id.child_id.sorted('sequence').mapped('url'), ['/shop'])

    def test_navbar_liquido_y_franja_visitanos(self):
        html = self.url_open('/').text
        self.assertIn('o_no_autohide_menu', html, 'Las tres opciones del menú nunca se esconden en el «+»')
        self.assertIn('id="dcasa-liquido"', html)
        self.assertNotIn('o_dcasa_anuncios', html, 'sin la barra de anuncios encima de la pastilla')
        # En la portada, la cobertura (sin mapa), que lleva a la página de contacto.
        self.assertIn('id="visitanos"', html)
        self.assertIn('href="/visitanos"', html)
        self.assertNotIn('https://www.google.com/maps/embed?pb=', html)

    def test_pagina_visitanos(self):
        """Tommalo vende 100% en línea: en lugar de la dirección y el mapa, su cobertura, su horario y sus canales."""
        website = self.env.ref('website.default_website')
        website.dcasa_whatsapp_number = '+507 6000-0002'
        website.social_instagram = 'https://www.instagram.com/tommalo-prueba'
        self.env.company.email = 'ventas@tommalo.example'
        respuesta = self.url_open('/visitanos')
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.text
        self.assertIn('Venta 100% en línea con entrega a domicilio en Panamá', html)
        self.assertIn('Vendemos en línea y te lo llevamos.', html)
        self.assertRegex(html, r'<a [^>]*href="https://api\.whatsapp\.com/send\?phone=50760000002&amp;text=[^"]*"'
                               r'[^>]*>\+507 6000-0002 ')
        self.assertIn('href="mailto:ventas@tommalo.example"', html)
        self.assertIn('href="https://www.instagram.com/tommalo-prueba"', html)
        self.assertIn('Escríbenos por WhatsApp', html)
        self.assertIn('<meta property="og:title" content="Contacto | Tommalo"/>', html)
        for sin_tienda in ('data-dcasa-mapa', 'google.com/maps', '<iframe', 'destination=',
                           'La Chorrera', "D'CASA", 'D&#39;CASA', 'dcasapty'):
            self.assertNotIn(sin_tienda, html)
        datos = json.loads(website._dcasa_json_ld())
        self.assertNotIn('geo', datos, 'Sin local: sin coordenadas')

    def test_visitanos_sin_datos_no_inventa_ninguno(self):
        """Sin WhatsApp, correo ni redes escritos (PENDIENTE), la página no muestra ninguno."""
        website = self.env.ref('website.default_website')
        website.dcasa_whatsapp_number = False
        self.env.company.write({'phone': False, 'email': False})
        html = self.url_open('/visitanos').text
        self.assertNotIn('mailto:', html)
        self.assertNotIn('instagram.com', html)
        self.assertNotIn('api.whatsapp.com/send?phone=', html)

    def test_menu_visitanos_viejo_se_actualiza(self):
        """Un sitio con el menú viejo (el ancla /#visitanos) queda con el actual: el contacto pasó al pie."""
        website = self.env.ref('website.default_website')
        self.env['website.menu'].create({'name': 'Visítanos', 'url': '/#visitanos', 'parent_id': website.menu_id.id,
                                         'website_id': website.id})
        self.env['website']._dcasa_armar_menu_principal()
        urls = website.menu_id.child_id.mapped('url')
        self.assertNotIn('/#visitanos', urls)
        self.assertNotIn('/visitanos', urls, 'el contacto va en el pie')
        self.assertIn('href="/visitanos"', self.url_open('/').text, 'y sigue a un clic, en el pie')

    def test_armar_menu_respeta_lo_agregado(self):
        website = self.env.ref('website.default_website')
        propio = self.env['website.menu'].create({
            'name': 'Ofertas', 'url': '/ofertas', 'parent_id': website.menu_id.id, 'website_id': website.id,
        })
        self.env['website']._dcasa_armar_menu_principal()
        self.env['website']._dcasa_armar_menu_principal()
        urls = website.menu_id.child_id.mapped('url')
        self.assertIn('/ofertas', urls, 'El menú que se agregó desde el editor se queda')
        self.assertEqual(urls.count('/shop'), 1, 'Sin duplicados al volver a correr')
        self.assertTrue(propio.exists())

    def test_cabecera_sobre_el_hero(self):
        self.assertIn('o_header_overlay', self.url_open('/').text)
        self.assertIn('o_header_overlay', self.url_open('/socios').text)
        self.assertIn('o_header_overlay', self.url_open('/contactus').text)
        self.assertNotIn('o_header_overlay', self.url_open('/shop').text)

    def test_contacto_con_datos_reales(self):
        self.env.company.email = 'ventas@tommalo.example'
        html = self.url_open('/contactus').text
        self.assertNotIn('Fake Buena Vista', html)
        self.assertNotIn('555-555-5556', html)
        self.assertIn('ventas@tommalo.example', html)
        self.assertIn('Venta 100% en línea con entrega a domicilio en Panamá', html)
        self.assertIn('href="/whatsapp"', html)

    def test_whatsapp_sin_boton_en_el_menu_y_con_la_cobertura(self):
        """«Escríbenos» no va en el menú. La portada lleva su cobertura: el WhatsApp de ventas, el horario y la zona; el
        contacto, en el pie."""
        website = self.env.ref('website.default_website')
        website.dcasa_whatsapp_number = '+507 6000-0002'
        self.assertNotIn('btn_cta', self.url_open('/shop').text, 'el menú ya no lleva «Escríbenos»')
        portada = self.url_open('/').text
        seccion = re.search(r'<section id="visitanos".*?</section>', portada, re.S)
        self.assertTrue(seccion, 'la portada trae la cobertura')
        self.assertIn('https://api.whatsapp.com/send?phone=50760000002', seccion.group(0))
        self.assertIn('+507 6000-0002', seccion.group(0))
        self.assertIn('Venta 100% en línea con entrega a domicilio en Panamá', seccion.group(0))
        pie = re.search(r'<footer.*?</footer>', portada, re.S).group(0)
        self.assertIn('href="/visitanos"', pie)

    def test_cache_de_pagina_separa_tarifas(self):
        pagina = self.env.ref('website.homepage_page')
        pedido = type('Pedido', (), {})()
        pedido.website = self.env.ref('website.default_website')
        pedido.lang = self.env['res.lang']._lang_get('en_US')
        pedido.httprequest = type('H', (), {'path': '/'})()
        pedido.session = type('S', (), {'debug': ''})()
        tarifas = self.env['product.pricelist'].create([{'name': 'A'}, {'name': 'B'}])
        claves = []
        for tarifa in tarifas:
            pedido.pricelist = tarifa
            pedido.fiscal_position = self.env['account.fiscal.position']
            claves.append(pagina._get_cache_key(pedido))
        self.assertNotEqual(*claves)


@tagged('post_install', '-at_install')
class TestCarritoReglas(HttpCase):
    """«Agregar» de un clic con la tienda solo para usuarios registrados."""

    def test_tienda_solo_registrados_no_agrega(self):
        website = self.env.ref('website.default_website')
        website.ecommerce_access = 'logged_in'
        producto = self.env['product.template'].create({
            'name': 'PRODUCTO DE PRUEBA', 'list_price': 50.0, 'is_published': True,
        })
        self.authenticate(None, None)
        # Sin acceso a la tienda la portada no ofrece «Agregar»: el token sale de otro formulario.
        self.assertNotIn('action="/dcasa/carrito/agregar"', self.url_open('/').text)
        socios = self.url_open('/socios').text
        token = re.search(r'name="csrf_token" value=[\'"]([^\'"]+)', socios).group(1)
        respuesta = self.url_open('/dcasa/carrito/agregar', data={
            'csrf_token': token, 'product_template_id': producto.id,
        }, allow_redirects=False)
        self.assertNotIn('/shop/cart', respuesta.headers.get('Location', ''))


@tagged('post_install', '-at_install')
class TestResenasRobustas(TransactionCase):

    def test_json_incompleto_no_tumba_la_portada(self):
        from odoo.addons.website_dcasa.models import website as modulo
        website = self.env.ref('website.default_website')
        original = modulo._leer_resenas
        try:
            modulo._leer_resenas = lambda: {'ficha': 'https://x', 'puntuacion': None,
                                            'opiniones': [{'autor': 'A', 'texto': 'Bien', 'estrellas': 5}]}
            self.assertEqual(website._dcasa_resenas()['copias'], 1)
            modulo._leer_resenas = lambda: {'opiniones': [{'texto': 'sin autor'}]}
            self.assertEqual(website._dcasa_resenas()['opiniones'], [])
        finally:
            modulo._leer_resenas = original


# Lo que ningún visitante debe leer en las páginas de este módulo (encargo del 2026-11-19): ni la marca de la tienda de
# origen ni nada de muebles. Se mira el texto visible y lo que también se lee o se oye: alt, title, aria-label,
# placeholder y las etiquetas <meta> (Google y las redes).
RESTOS_DE_DCASA = re.compile(
    r"D'CASA|D&#39;CASA|D&apos;CASA|D’CASA|dcasapty|mueble|colch[oó]n|La Chorrera|Baby Caleb|Nateen|pañal|bebé", re.I)


def _lo_que_se_ve(html):
    sin_codigo = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', ' ', html, flags=re.S)
    textos = re.sub(r'<[^>]+>', ' ', sin_codigo)
    atributos = re.findall(r'\b(?:alt|title|aria-label|placeholder)="([^"]*)"', sin_codigo)
    metas = re.findall(r'<meta[^>]*\bcontent="([^"]*)"', sin_codigo)
    return ' '.join([textos, *atributos, *metas])


@tagged('post_install', '-at_install')
class TestSinRestosDeDcasa(HttpCase):
    """Ni «Tommalo» ni nada de muebles en lo que se ve del sitio (los textos legales van palabra por palabra y los dicta
    el dueño: no se miran aquí; /socios es de dcasa_socios)."""

    def setUp(self):
        super().setUp()
        self.website = self.env.ref('website.default_website')
        self.producto = self.env['product.template'].create({
            'name': 'Crema de la prueba de restos', 'list_price': 45.0, 'is_published': True,
            'dcasa_black_weekend': True})

    def test_ninguna_pagina_dice_nada_de_otros_negocios(self):
        from odoo.addons.website_dcasa.models.black_weekend import PARAM_ACTIVO, PARAM_FIN, PARAM_INICIO
        param = self.env['ir.config_parameter'].sudo()
        param.set_param(PARAM_ACTIVO, '1')
        param.set_param(PARAM_INICIO, '')
        param.set_param(PARAM_FIN, '')
        for ruta in ('/', '/shop', self.producto.website_url, '/visitanos', '/contactus', '/web/login',
                     '/promociones', '/shop/cart', '/shop?search=zzzz', '/esta-pagina-no-existe'):
            with self.subTest(ruta=ruta):
                respuesta = self.url_open(ruta)
                self.assertIn(respuesta.status_code, (200, 404))
                encontrado = RESTOS_DE_DCASA.findall(_lo_que_se_ve(respuesta.text))
                self.assertEqual(encontrado, [], ruta)

    def test_el_checkout_no_dice_el_lugar_ni_muebles(self):
        """Las entregas y el mensaje del pago en la tienda: lo que el cliente lee al pagar."""
        entregas = self.env['delivery.carrier'].sudo().search([('is_published', '=', True)])
        for nombre in entregas.mapped('name'):
            self.assertNotRegex(nombre, RESTOS_DE_DCASA)
        cod = self.env.ref('delivery.payment_provider_cod').sudo()
        self.assertNotRegex(str(cod.with_context(lang='es_419').pending_msg), RESTOS_DE_DCASA)

    def test_una_base_ya_instalada_queda_al_dia_al_actualizar(self):
        """El menú se arma una vez al instalar y las entregas también: en una base que ya existía (staging) la migración
        19.0.1.19.0 los pone al día. Aquí se simula esa base vieja (con un nombre de entrega de PRUEBA) y se corre lo
        que corre la migración."""
        from unittest.mock import patch  # noqa: PLC0415

        from odoo.addons.website_dcasa.models import tienda  # noqa: PLC0415
        idiomas = [codigo for codigo, _n in self.env['res.lang'].get_installed()]
        socios = self.website.menu_id.child_id.filtered(lambda m: m.url == '/socios')
        socios = socios or self.env['website.menu'].create({
            'name': 'Socios de prueba', 'url': '/socios', 'parent_id': self.website.menu_id.id,
            'website_id': self.website.id})
        Carrier = self.env['delivery.carrier'].sudo().with_context(active_test=False)
        retiro = Carrier.search([('name', '=', 'Retiro en tienda')])
        retiro.update_field_translations('name', dict.fromkeys(idiomas, 'Retiro en tienda (nombre viejo de prueba)'))

        with patch.dict(tienda.ENTREGAS_ANTES, {'Retiro en tienda (nombre viejo de prueba)': 'Retiro en tienda'}):
            self.env['website']._dcasa_sin_restos_de_dcasa()
            self.env['website']._dcasa_sin_restos_de_dcasa()   # se puede volver a correr

        self.assertFalse(socios.exists(), 'Socios ya no va en el menú (sigue en el pie)')
        for idioma in idiomas:
            with self.subTest(idioma=idioma):
                self.assertEqual(retiro.with_context(lang=idioma).name, 'Retiro en tienda')
        self.assertEqual(Carrier.search_count([('name', 'ilike', 'Retiro en tienda')]), 1, 'sin duplicar la entrega')
        cabecera = re.search(r'<header id="top".*?</header>', self.url_open('/shop').text, re.S).group(0)
        self.assertNotRegex(cabecera, RESTOS_DE_DCASA)
        self.assertIn('<span>Productos</span>', cabecera)
        # La migración llama justo a esto.
        with file_open('website_dcasa/migrations/19.0.1.19.0/post-migrate.py') as archivo:
            self.assertIn('_dcasa_sin_restos_de_dcasa()', archivo.read())
