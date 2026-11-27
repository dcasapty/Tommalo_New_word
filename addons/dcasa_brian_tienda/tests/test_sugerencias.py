"""Sugerencias del saludo con el catálogo («opción 2»): las dos categorías de la portada con más productos publicados,
en la respuesta del pase (NOMBRE_SUGERENCIA, vacío en Tommalo: sale el nombre de la categoría). Con empate, el orden de la portada; sin nada publicado, ninguna (la página usa las de fábrica)."""
from odoo import Command
from odoo.tests import tagged

from .common import TiendaCase


@tagged('post_install', '-at_install')
class TestSugerenciasDelSaludo(TiendaCase):

    def _publicar(self, clave, cuantos):
        categoria = self.env.ref(f'website_dcasa.public_category_{clave}')
        for i in range(cuantos):
            self.env['product.template'].create({
                'name': f'ZZSUG {clave} {i}', 'list_price': 10.0, 'sale_ok': True, 'is_published': True,
                'public_categ_ids': [Command.set(categoria.ids)]})

    def _sugerencias(self):
        respuesta = self.post('pase').json()
        self.assertTrue(respuesta['ok'], respuesta)
        return respuesta['sugerencias']

    def test_las_dos_categorias_con_mas_productos(self):
        Plantilla = self.env['product.template']
        Plantilla.search([('is_published', '=', True)]).write({'is_published': False})
        self._publicar('salud', 3)
        self._publicar('hogar', 2)
        self._publicar('belleza', 1)
        self.assertEqual(self._sugerencias(), ['Salud', 'Hogar'])
        self._publicar('belleza', 3)
        self.assertEqual(self._sugerencias(), ['Belleza', 'Salud'], 'cambia sola al publicar más')
        self._publicar('salud', 1)
        self.assertEqual(self._sugerencias(), ['Belleza', 'Salud'], 'con empate, el orden de la portada')
        otro = self.env.ref('website_dcasa.public_category_otro')
        Plantilla.create({'name': 'ZZSUG oculto', 'list_price': 10.0, 'sale_ok': True, 'is_published': False,
                          'public_categ_ids': [Command.set(otro.ids)]})
        self.assertNotIn('Otros', self._sugerencias(), 'lo no publicado no cuenta')
        Plantilla.search([('is_published', '=', True)]).write({'is_published': False})
        self.assertEqual(self._sugerencias(), [], 'sin nada publicado, ninguna: la página usa las de fábrica')


@tagged('post_install', '-at_install')
class TestVitrinaSugerida(TiendaCase):
    """La vitrina del chat ampliado sin productos de la conversación: «Lo más
    buscado» de la portada, sin lo que ya está en el carrito, lo agotado al final y a lo sumo seis tarjetas."""

    def test_lo_mas_buscado_sin_lo_del_carrito(self):
        self.jabon.website_sequence = -99999   # primero en «Lo más buscado»
        primero = self.url_open('/dcasa/brian/v1/vitrina').json()
        self.assertTrue(primero['ok'])
        self.assertLessEqual(len(primero['productos']), 6)
        self.assertEqual(primero['productos'][0]['plantilla_id'], self.jabon.id)
        self.assertEqual(set(primero['productos'][0]), {'producto_id', 'plantilla_id', 'nombre', 'precio_texto',
                                                        'disponibilidad', 'imagen', 'ruta', 'agregable'})
        agregado = self.post('carrito/agregar', {'producto_id': self.jabon.product_variant_id.id, 'cantidad': 1})
        self.assertTrue(agregado.json()['ok'], agregado.text)
        despues = self.url_open('/dcasa/brian/v1/vitrina').json()['productos']
        sugeridos = [p['plantilla_id'] for p in despues]
        self.assertNotIn(self.jabon.id, sugeridos, 'lo que ya está en el carrito no se sugiere')
        estados = [p['disponibilidad'] for p in despues]
        self.assertEqual(estados, sorted(estados, key=lambda e: e == 'agotado'), 'lo agotado, al final')

    def test_apagado_no_sugiere(self):
        self.env['ir.config_parameter'].sudo().set_param('dcasa_brian_tienda.activo', 'False')
        self.assertEqual(self.url_open('/dcasa/brian/v1/vitrina').json(), {'ok': False, 'motivo': 'apagado'})
