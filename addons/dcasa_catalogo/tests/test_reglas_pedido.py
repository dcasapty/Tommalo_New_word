from odoo.addons.dcasa_catalogo.catalogo import PARAM_STOCK_PRUEBA, aplicar_stock_prueba
from odoo.addons.dcasa_catalogo.reglas import (
    asignar_foto,
    codigo_del_pedido,
    fila_para_comparar,
    precio_terminado_en_99,
)
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReglasPedido(TransactionCase):
    """Reglas sin Odoo: precio .99, código aparte y a qué fila va cada foto."""

    def test_precios_terminan_en_99(self):
        self.assertEqual(precio_terminado_en_99(318.66), 318.99)
        self.assertEqual(precio_terminado_en_99(318.65999999999997), 318.99, 'Así viene del Excel')
        self.assertEqual(precio_terminado_en_99(439.98), 439.99)
        self.assertEqual(precio_terminado_en_99(186.64), 186.99)
        self.assertEqual(precio_terminado_en_99(129.99), 129.99, 'Ya termina en .99: igual')
        self.assertEqual(precio_terminado_en_99(100), 100.99, 'Se conserva la parte entera')
        self.assertIsNone(precio_terminado_en_99(None), 'Celda vacía: no se inventa un precio')

    def test_codigo_que_ya_existe_va_aparte(self):
        self.assertEqual(codigo_del_pedido('ZZ0300300', {'ZZ0300300'}, 'LOTE07'), 'ZZ0300300-LOTE07')
        self.assertEqual(codigo_del_pedido('ZZ91K', {'ZZ0300300'}, 'LOTE07'), 'ZZ91K')

    def filas(self):
        datos = [
            ('ZZ91K', 'Pieza tapizada King – beige', '203 × 193 × 123 cm'),
            ('ZZ91K', 'Pieza tapizada King – negro', '203 × 193 × 123 cm'),
            ('ZZ91K', 'Pieza tapizada King – gris', '203 × 193 × 123 cm'),
            ('ZZ82Q', 'Pieza tapizada Queen – beige', '213 × 158 × 120 cm'),
            ('ZZ83Q', 'Pieza tapizada Queen – beige', '213 × 158 × 120 cm'),
            ('ZZ84F', 'Pieza tapizada Full – blanco', '193 × 135 × 110 cm'),
            ('ZZ85Q', 'Pieza tapizada Queen – crema', '205 × 151 × 110 cm'),
            ('ZZ-BF-022-N-F-1-W', 'Pieza tapizada Full – blanco', 'Full'),
            ('ZZ0400300-Q', 'Pieza tapizada Queen – tela negra', '205 × 151 × 110 cm'),
            ('ZZ0400400-Q', 'Pieza tapizada Queen – tela marrón', '205 × 151 × 110 cm'),
        ]
        return [fila_para_comparar(*d) for d in datos]

    def test_foto_por_codigo(self):
        filas = self.filas()
        r = asignar_foto('ZZ91K Pieza tapizada King – Gris 203 × 193 × 123 cm.jpg', filas)
        self.assertEqual((r['fila'], r['como']), (2, 'codigo'), 'Código con varios colores: manda el color')
        r = asignar_foto('ZZ-BF-022-N-F-1-W.jpg', filas)
        self.assertEqual((r['fila'], r['como']), (7, 'codigo'))
        r = asignar_foto('ZZ91K Pieza tapizada King.jpg', filas)
        self.assertIsNone(r['fila'], 'Sin color no se sabe de cuál de los tres es')

    def test_foto_por_descripcion(self):
        filas = self.filas()
        r = asignar_foto('Pieza tapizada Queen – crema 205 × 151 × 110 cm.jpg', filas)
        self.assertEqual((filas[r['fila']]['codigo'], r['como']), ('ZZ85Q', 'descripcion'))
        r = asignar_foto('Pieza tapizada Full – blanco 193 × 135 × 110 cm.jpg', filas)
        self.assertEqual(filas[r['fila']]['codigo'], 'ZZ84F', 'Las medidas descartan al Full blanco sin medidas')

    def test_foto_dudosa_no_se_adivina(self):
        filas = self.filas()
        archivo = 'Pieza tapizada Queen – beige 213 × 158 × 120 cm.jpg'
        r = asignar_foto(archivo, filas)
        self.assertEqual((r['fila'], r['como']), (None, 'ambigua'))
        self.assertIn('ZZ82Q', r['nota'])
        self.assertIn('ZZ83Q', r['nota'])
        r = asignar_foto(archivo, filas, {archivo: ('ZZ83Q', None, 'cabecero de canales')})
        self.assertEqual((filas[r['fila']]['codigo'], r['como']), ('ZZ83Q', 'decision'))
        self.assertEqual(asignar_foto('foto.jpg', filas)['como'], 'sin_coincidencia')

    def test_color_del_archivo_distinto_queda_avisado(self):
        filas = self.filas()
        archivo = 'ZZ0400300-Q  Queen tela marron205×151×110 cm.jpg'
        r = asignar_foto(archivo, filas)
        self.assertEqual(filas[r['fila']]['codigo'], 'ZZ0400300-Q')
        self.assertIn('marron', r['nota'], 'Se asigna por código, pero queda el aviso en el reporte')
        r = asignar_foto(archivo, filas, {archivo: ('ZZ0400400-Q', None, 'la pieza es marrón')})
        self.assertEqual(filas[r['fila']]['codigo'], 'ZZ0400400-Q')


@tagged('post_install', '-at_install')
class TestStockDePrueba(TransactionCase):
    """Existencias de prueba (solo staging) para lo que nunca tuvo stock, también lo del catálogo."""

    def test_stock_de_prueba(self):
        Producto = self.env['product.product']
        ubicacion = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.ref('base.main_company').id)], limit=1).lot_stock_id
        sin_nada = Producto.create({'name': 'Nuevo sin stock', 'is_storable': True})
        contado = Producto.create({'name': 'Contado', 'is_storable': True})
        vendido = Producto.create({'name': 'Vendido (0 con movimientos)', 'is_storable': True})
        Quant = self.env['stock.quant'].with_context(inventory_mode=True)

        def contar(producto, cantidad):
            Quant.create({'product_id': producto.id, 'location_id': ubicacion.id,
                          'inventory_quantity': cantidad})._apply_inventory()

        contar(contado, 3)
        contar(vendido, 2)
        contar(vendido, 0)
        # Un producto «del catálogo» (de prueba) que llegó en 0, sin movimientos.
        del_catalogo = Producto.create({'name': 'Producto de catálogo de prueba', 'default_code': 'ZZ-CAT-0',
                                        'is_storable': True})
        self.assertFalse(self.env['stock.move'].search_count([('product_id', '=', del_catalogo.id)]))

        parametros = self.env['ir.config_parameter'].sudo()
        parametros.set_param(PARAM_STOCK_PRUEBA, '0')
        self.assertEqual(aplicar_stock_prueba(self.env), 0, 'En 0 (producción) no hace nada')
        self.assertEqual(sin_nada.qty_available, 0)

        parametros.set_param(PARAM_STOCK_PRUEBA, '10')
        self.assertGreater(aplicar_stock_prueba(self.env), 0)
        self.env.invalidate_all()
        self.assertEqual(sin_nada.qty_available, 10)
        self.assertEqual(del_catalogo.qty_available, 10, 'También los productos del catálogo')
        self.assertEqual(contado.qty_available, 3, 'Un conteo real no se pisa')
        self.assertEqual(vendido.qty_available, 0, 'Con movimientos no se toca')
        self.assertEqual(aplicar_stock_prueba(self.env), 0, 'Idempotente')
        self.assertEqual(sin_nada.qty_available, 10)
