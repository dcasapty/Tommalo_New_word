"""La portada neutra y lo que ya no existe: las páginas de marketing de la plantilla de origen (beneficios, historia,
tips, cómo comprar, preguntas frecuentes) se quitaron por completo; la banda final es genérica; y
``_dcasa_hero_tarjeta``
sigue funcionando (sin nada publicado, no sale)."""
import re

from odoo.tests import HttpCase, tagged

RUTAS_QUITADAS = ('/beneficios', '/historia', '/tips', '/como-comprar', '/faq')
DE_OTROS = ("D'CASA", 'D&#39;CASA', 'dcasapty', 'La Chorrera', 'Baby Caleb', 'Nateen', 'bebé', 'pañal', 'mueble')


@tagged('post_install', '-at_install')
class TestPaginasTommalo(HttpCase):

    def test_las_paginas_de_marketing_no_existen(self):
        for ruta in RUTAS_QUITADAS:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.url_open(ruta).status_code, 404)

    def test_ninguna_ruta_ni_vista_de_marketing(self):
        for xmlid in ('pagina_beneficios', 'pagina_historia', 'pagina_tips', 'pagina_como_comprar', 'pagina_faq',
                      'seccion_sellos', 'seccion_educacion', 'seccion_testimonios', 'seccion_diferenciadores',
                      'seccion_historia', 'seccion_tips', 'seccion_como_comprar', 'seccion_preguntas'):
            with self.subTest(xmlid=xmlid):
                self.assertFalse(self.env.ref(f'website_dcasa.{xmlid}', raise_if_not_found=False))

    def test_sitemap_sin_las_paginas_quitadas(self):
        mapa = self.url_open('/sitemap.xml').text
        for ruta in RUTAS_QUITADAS:
            self.assertNotIn(f'{ruta}</loc>', mapa)

    def test_el_menu_y_el_pie_no_enlazan_a_las_paginas_quitadas(self):
        html = self.url_open('/').text
        for ruta in RUTAS_QUITADAS:
            self.assertNotIn(f'href="{ruta}"', html)

    def test_banda_final_generica(self):
        html = self.url_open('/').text
        banda = re.search(r'<section class="o_dcasa_cta_final".*?</section>', html, re.S)
        self.assertTrue(banda, 'la portada cierra con la banda final')
        self.assertIn('Ver el catálogo', banda.group(0))
        self.assertIn('href="/shop"', banda.group(0))
        for de_otros in DE_OTROS:
            self.assertNotIn(de_otros, banda.group(0))


@tagged('post_install', '-at_install')
class TestTarjetaDelHero(HttpCase):
    """``_dcasa_hero_tarjeta``: el producto publicado más barato, leído de Odoo; con el catálogo vacío no sale nada. La
    portada no la dibuja (sin tarjeta fija de producto)."""

    def _producto(self, nombre, precio, publicado=True):
        return self.env['product.template'].create({
            'name': nombre, 'list_price': precio, 'sale_ok': True, 'is_published': publicado, 'type': 'consu',
        })

    def setUp(self):
        super().setUp()
        self.env['product.template'].sudo().search([]).write({'is_published': False})

    def test_sin_nada_publicado_no_sale(self):
        self.assertFalse(self.env.ref('website.default_website')._dcasa_hero_tarjeta())

    def test_el_mas_barato_de_los_publicados(self):
        self._producto('Crema de prueba', 50)
        barata = self._producto('Lámpara de prueba', 45)
        self._producto('Producto de prueba sin publicar', 10, publicado=False)
        tarjeta = self.env.ref('website.default_website')._dcasa_hero_tarjeta()
        self.assertTrue(tarjeta)
        self.assertEqual(tarjeta['desde'], 45)
        self.assertEqual(tarjeta['nombre'].lower(), 'lámpara de prueba')
        self.assertEqual(tarjeta['url'], barata.website_url)

    def test_la_portada_no_dibuja_tarjeta_fija(self):
        self._producto('Crema de prueba', 50)
        self.assertNotIn('o_dcasa_hero_tarjeta', self.url_open('/').text)
