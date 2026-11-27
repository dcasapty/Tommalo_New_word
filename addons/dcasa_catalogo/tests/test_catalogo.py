import base64
import io
import os
from unittest.mock import patch
from urllib.parse import unquote

from PIL import Image

from odoo.addons.dcasa_base.nombres import nombre_en_mayusculas
from odoo.addons.dcasa_catalogo import catalogo as C
from odoo.addons.dcasa_catalogo import reglas
from odoo.addons.dcasa_catalogo.catalogo import cargar_catalogo, leer_catalogo, xmlid_de
from odoo.addons.dcasa_catalogo.models import combo_armable
from odoo.addons.dcasa_catalogo.reglas import categoria_de_nombre
from odoo.modules.module import get_module_path
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools.misc import file_open

CATEGORIAS = {'belleza': 'Belleza', 'hogar': 'Hogar', 'salud': 'Salud', 'otro': 'Otros'}
ATRIBUTO = 'Presentación de prueba'


def _foto(color):
    """Un JPEG de 8×8 de un solo color, en base64: las pruebas no necesitan fotos reales (y el repositorio no trae)."""
    archivo = io.BytesIO()
    Image.new('RGB', (8, 8), color).save(archivo, 'JPEG')
    return base64.b64encode(archivo.getvalue())


def _item(clave, variantes, atributo=None, **otros):
    """Un producto del JSON para las pruebas de la carga (con datos de prueba, no de un negocio)."""
    item = {'clave': clave, 'nombre': f'Producto de prueba {clave}', 'categoria': 'belleza', 'orden': 99,
            'descripcion': None, 'variantes': variantes}
    if atributo:
        item['atributo'] = atributo
    item.update(otros)
    return item


def _catalogo(*productos, atributos=None):
    return {'fuente': 'Lista de prueba', 'atributos': atributos or {ATRIBUTO: ['CH', 'MED', 'GR']},
            'productos': list(productos)}


@tagged('post_install', '-at_install')
class TestCatalogoVacioAProposito(TransactionCase):
    """El catálogo de Tommalo está vacío a propósito (PENDIENTE): nada de otros negocios y todo listo para cargarlo."""

    def test_instala_sin_productos_de_catalogo(self):
        propios = self.env['ir.model.data'].search([
            ('module', '=', 'dcasa_catalogo'), ('model', '=', 'product.template')])
        self.assertFalse(propios.mapped('name'), 'ningún producto con xmlid dcasa_catalogo.producto_*')
        self.assertFalse(self.env['ir.model.data'].search_count([
            ('module', '=', 'dcasa_catalogo'), ('name', '=like', 'producto\\_%')]))
        self.assertFalse(self.env['product.template'].with_context(active_test=False).search([
            ('dcasa_black_weekend', '=', True)]))

    def test_el_archivo_del_catalogo_esta_vacio(self):
        catalogo = leer_catalogo()
        self.assertEqual(catalogo['productos'], [])
        self.assertEqual(catalogo['atributos'], {})
        self.assertEqual(cargar_catalogo(self.env), 0, 'cargar un catálogo vacío no crea nada')

    def test_no_hay_fotos_en_el_modulo(self):
        carpeta = os.path.join(get_module_path('dcasa_catalogo'), 'data', 'fotos')
        self.assertEqual(os.listdir(carpeta) if os.path.isdir(carpeta) else [], [], 'sin fotos en data/fotos')
        self.assertFalse(os.path.exists(os.path.join(get_module_path('dcasa_catalogo'), 'static', 'img', 'productos')))

    def test_sin_selecciones_ni_precios_de_otro_negocio(self):
        self.assertEqual(C.BLACK_WEEKEND, [])
        self.assertEqual(combo_armable.PRECIOS_COMBO_APROBADOS, {})
        self.assertEqual(reglas.CATEGORIAS, [])
        with file_open('dcasa_catalogo/data/inventario_anterior.csv', 'r') as archivo:
            self.assertEqual(len(archivo.read().splitlines()), 1, 'Del inventario anterior: solo el encabezado')

    def test_las_cuatro_categorias_existen(self):
        for clave, nombre in CATEGORIAS.items():
            interna = self.env.ref(f'dcasa_catalogo.product_category_{clave}')
            self.assertEqual(interna.name, nombre, clave)
            publica = self.env.ref(f'website_dcasa.public_category_{clave}')
            self.assertEqual(publica.name, nombre, clave)
            self.assertEqual(C.categoria_web(self.env, clave), publica)
            self.assertEqual(self.env.ref(C.CATEGORIA_INTERNA[clave]), interna)
        self.assertEqual(set(C.CATEGORIA_INTERNA), set(CATEGORIAS))
        self.assertEqual(set(C.CATEGORIA_WEB), set(CATEGORIAS))

    def test_las_categorias_de_los_negocios_de_origen_ya_no_existen(self):
        for viejo in ('product_category_panales', 'product_category_toallitas', 'product_category_fulares',
                      'product_category_zapateras', 'product_category_organizacion', 'product_category_oficina'):
            self.assertFalse(self.env.ref(f'dcasa_catalogo.{viejo}', raise_if_not_found=False), viejo)
        for viejo in ('public_category_panales', 'public_category_toallitas', 'public_category_fulares',
                      'public_category_colchones', 'public_category_muebles_tv'):
            self.assertFalse(self.env.ref(f'website_dcasa.{viejo}', raise_if_not_found=False), viejo)

    def test_lo_agotado_no_se_pide(self):
        """Lo agotado no se pide en la web: también un producto nuevo hecho a mano."""
        nuevo = self.env['product.template'].create({'name': 'Producto nuevo de prueba', 'is_storable': True})
        self.assertFalse(nuevo.allow_out_of_stock_order)
        self.assertFalse(self.env['product.template'].search_count([('allow_out_of_stock_order', '=', True)]))


@tagged('post_install', '-at_install')
class TestCatalogoConProductosDePrueba(TransactionCase):
    """Lo que debe hacer la carga cuando el catálogo ya tenga productos, con productos inventados y marcados de prueba."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')
        cls.ubicacion = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1).lot_stock_id
        cls.Variante = cls.env['product.product'].with_context(active_test=False)
        cls.lista = {
            'ZZ-CREMA-CH': ('Frasco chico de prueba — 50 ml', 9.99, 3),
            'ZZ-CREMA-GR': ('Frasco grande de prueba — 120 ml', 12.50, 0),
            'ZZ-LAMPARA': ('Lámpara de mesa de prueba — caja de 1', 45.00, 5),
            'ZZ-VITAMINA': ('Frasco de prueba — 60 cápsulas', 20.00, 2),
            'ZZ-OTRO': ('Artículo de prueba', 7.00, 0),
        }
        cls.productos = {
            'zz-crema': ('Crema de prueba', 'belleza', [('CH', 'ZZ-CREMA-CH'), ('GR', 'ZZ-CREMA-GR')]),
            'zz-lampara': ('Lámpara de prueba', 'hogar', [(None, 'ZZ-LAMPARA')]),
            'zz-vitamina': ('Vitaminas de prueba', 'salud', [(None, 'ZZ-VITAMINA')]),
            'zz-otro': ('Artículo de prueba', 'otro', [(None, 'ZZ-OTRO')]),
        }
        items = []
        for clave, (nombre, categoria, variantes) in cls.productos.items():
            datos = []
            for valor, codigo in variantes:
                texto, precio, existencias = cls.lista[codigo]
                dato = {'codigo': codigo, 'precio': precio, 'existencias': existencias, 'texto': texto}
                if valor:
                    dato['valor'] = valor
                datos.append(dato)
            items.append({'clave': clave, 'nombre': nombre, 'categoria': categoria, 'orden': len(items) + 1,
                          'descripcion': None, 'variantes': datos, **({'atributo': ATRIBUTO} if variantes[0][0] else {})})
        cls.catalogo = _catalogo(*items)
        cls.creados = cargar_catalogo(cls.env, cls.catalogo)

    def producto(self, clave):
        return self.env.ref(f'dcasa_catalogo.{xmlid_de(clave)}')

    def variante(self, codigo):
        variante = self.Variante.search([('default_code', '=', codigo)])
        self.assertEqual(len(variante), 1, codigo)
        return variante

    def test_cada_variante_con_su_codigo_precio_existencias_y_texto(self):
        self.assertEqual(self.creados, len(self.productos))
        impuesto = self.company.account_sale_tax_id
        for codigo, (texto, precio, existencias) in self.lista.items():
            variante = self.variante(codigo)
            self.assertEqual(variante.lst_price, precio, f'{codigo}: el precio exacto de la lista')
            self.assertEqual(variante.with_context(location=self.ubicacion.id).qty_available, existencias, codigo)
            self.assertEqual(variante.dcasa_presentacion, texto, f'{codigo}: el texto del dueño, tal cual')
            self.assertEqual(variante.taxes_id, impuesto, f'{codigo}: el ITBMS de venta de la empresa')
            self.assertTrue(variante.is_storable and variante.sale_ok, codigo)

    def test_agrupados_con_variantes(self):
        atributo = self.env['product.attribute'].search([('name', '=', ATRIBUTO)])
        self.assertEqual(len(atributo), 1)
        self.assertEqual(atributo.create_variant, 'always')
        for clave, (nombre, _categoria, variantes) in self.productos.items():
            producto = self.producto(clave)
            self.assertEqual(producto.name, nombre_en_mayusculas(nombre))
            self.assertEqual(producto.product_variant_count, len(variantes), clave)
            if variantes[0][0] is None:
                self.assertFalse(producto.attribute_line_ids, f'{clave}: producto simple')
                self.assertEqual(producto.default_code, variantes[0][1])
                continue
            self.assertEqual(producto.attribute_line_ids.attribute_id, atributo, clave)
            self.assertEqual(producto.attribute_line_ids.product_template_value_ids.sorted().mapped('name'),
                             [valor for valor, _codigo in variantes], clave)
            for valor, codigo in variantes:
                self.assertEqual(self.variante(codigo).product_template_attribute_value_ids.name, valor, codigo)

    def test_precio_de_lista_y_el_itbms_que_se_suma(self):
        """El precio de la lista es el de lista y el ITBMS de la empresa se suma."""
        producto = self.producto('zz-crema')
        self.assertEqual(producto.list_price, 9.99, 'El de la variante más barata; la otra, con su extra')
        impuesto = producto.taxes_id
        self.assertEqual(impuesto, self.company.account_sale_tax_id, 'El impuesto por defecto')
        self.assertFalse(impuesto.price_include)
        self.assertEqual(impuesto.amount, 7)
        orden = self.env['sale.order'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Clienta de prueba'}).id,
            'order_line': [(0, 0, {'product_id': self.variante('ZZ-LAMPARA').id}),
                           (0, 0, {'product_id': self.variante('ZZ-CREMA-GR').id})],
        })
        self.assertEqual(orden.order_line.mapped('price_unit'), [45.0, 12.5])
        self.assertAlmostEqual(orden.amount_untaxed, 57.5, places=2)
        self.assertAlmostEqual(orden.amount_tax, 4.03, places=2)
        self.assertAlmostEqual(orden.amount_total, 61.53, places=2)
        self.assertEqual(self.env['website'].get_current_website().show_line_subtotals_tax_selection,
                         'tax_excluded')

    def test_categorias_de_tommalo(self):
        for clave, (_nombre, categoria, _variantes) in self.productos.items():
            producto = self.producto(clave)
            self.assertEqual(producto.categ_id, self.env.ref(f'dcasa_catalogo.product_category_{categoria}'), clave)
            self.assertEqual(producto.public_categ_ids, self.env.ref(f'website_dcasa.public_category_{categoria}'),
                             clave)

    def test_presentacion_a_la_vista(self):
        crema = self.producto('zz-crema')
        lampara = self.producto('zz-lampara')
        self.assertEqual(lampara.dcasa_presentacion, self.lista['ZZ-LAMPARA'][0], 'Una sola variante: en la ficha')
        self.assertFalse(crema.dcasa_presentacion, 'Con varias variantes, cada una tiene la suya')
        lampara.dcasa_presentacion = 'Lámpara de prueba negra'
        self.assertEqual(lampara.product_variant_id.dcasa_presentacion, 'Lámpara de prueba negra',
                         'Se edita desde la ficha')
        # En el orden de los valores del atributo, no en el del código.
        self.assertEqual([texto for _v, texto in crema._dcasa_presentaciones()],
                         [self.lista['ZZ-CREMA-CH'][0], self.lista['ZZ-CREMA-GR'][0]])

    def test_las_vistas_muestran_la_presentacion(self):
        for modelo, xmlid, tipo in (('product.template', 'product.product_template_only_form_view', 'form'),
                                    ('product.product', 'product.product_normal_form_view', 'form'),
                                    ('product.product', 'product.product_variant_easy_edit_view', 'form'),
                                    ('product.product', 'product.product_product_tree_view', 'list')):
            arch = self.env[modelo].get_view(self.env.ref(xmlid).id, tipo)['arch']
            self.assertIn('name="dcasa_presentacion"', arch, xmlid)

    def test_los_productos_nuevos_no_se_publican_sin_foto(self):
        for clave in self.productos:
            producto = self.producto(clave)
            self.assertFalse(producto.allow_out_of_stock_order, f'{clave}: lo agotado no se pide')
            self.assertFalse(producto.is_published, f'{clave}: sin foto no sale en la web')

    def test_existencias_con_su_motivo_solo_al_crear(self):
        movimientos = self.env['stock.move'].search([('product_id', '=', self.variante('ZZ-LAMPARA').id)])
        self.assertEqual(movimientos.mapped('inventory_name'),
                         ['Existencias iniciales del catálogo (Lista de prueba)'])
        self.assertFalse(self.env['stock.move'].search_count([('product_id', '=', self.variante('ZZ-OTRO').id)]),
                         'En 0 no hace falta ajuste')

    def test_idempotente_y_respeta_cambios(self):
        producto = self.producto('zz-vitamina')
        producto.list_price = 1  # el dueño lo cambió en Odoo
        variante = self.variante('ZZ-LAMPARA')
        self.env['stock.quant'].with_context(inventory_mode=True, inventory_name='Conteo de prueba').create({
            'product_id': variante.id, 'location_id': self.ubicacion.id, 'inventory_quantity': 1})._apply_inventory()
        antes = self.env['product.template'].search_count([])
        self.assertEqual(cargar_catalogo(self.env, self.catalogo), 0)
        self.assertEqual(self.env['product.template'].search_count([]), antes)
        self.assertEqual(producto.list_price, 1)
        self.assertEqual(variante.with_context(location=self.ubicacion.id).qty_available, 1, 'Un conteo no se pisa')

    def test_nombres_distintos(self):
        """Ni la clienta ni la vendedora deben ver dos productos con el mismo nombre."""
        nombres = [self.producto(clave).name.lower() for clave in self.productos]
        self.assertEqual(len(nombres), len(set(nombres)))

    def test_busqueda_por_varias_palabras(self):
        encontrados = self.env['product.product'].search([('display_name', 'ilike', 'crema prueba')])
        self.assertIn(self.variante('ZZ-CREMA-CH'), encontrados)
        self.assertIn(self.variante('ZZ-CREMA-GR'), encontrados)
        self.assertNotIn(self.variante('ZZ-LAMPARA'), encontrados)

    def test_cotizacion_por_whatsapp(self):
        cliente = self.env['res.partner'].create({'name': 'Ana de prueba', 'phone': '6000-0001'})
        orden = self.env['sale.order'].create({
            'partner_id': cliente.id,
            'order_line': [(0, 0, {'product_id': self.variante('ZZ-LAMPARA').id})],
        })
        accion = orden.action_dcasa_whatsapp()
        self.assertTrue(accion['url'].startswith('https://api.whatsapp.com/send?phone=50760000001&text='))
        self.assertIn(orden.name, accion['url'])
        self.assertEqual(orden.state, 'sent')
        # El mensaje dice la empresa (Ajustes › Empresa), nunca el nombre de la plantilla de origen.
        texto = unquote(accion['url'].split('&text=', 1)[1])
        self.assertIn(f' de {orden.company_id.name} por ', texto)
        self.assertNotIn("D'CASA", texto)

    def test_migracion_pasa_del_incluido_al_que_se_suma(self):
        """Bases cargadas con «ITBMS 7% incluido»: cambia el impuesto, no el precio."""
        venta = self.company.account_sale_tax_id
        incluido = venta.copy({'name': 'ITBMS 7% incluido', 'price_include_override': 'tax_included'})
        viejo = self.producto('zz-crema') | self.producto('zz-lampara')
        a_mano = self.producto('zz-vitamina')
        exento = self.env['account.tax'].create({'name': 'Exento prueba', 'amount': 0, 'type_tax_use': 'sale'})
        viejo.taxes_id = incluido
        a_mano.taxes_id = exento  # el dueño le puso otro impuesto: no se toca
        precios = {p: (p.list_price, p.product_variant_ids.mapped('lst_price')) for p in viejo | a_mano}
        self.env['website'].search([]).show_line_subtotals_tax_selection = 'tax_included'

        self.assertEqual(C.pasar_a_itbms_que_se_suma(self.env), 2)
        self.assertEqual(viejo.taxes_id, venta)
        self.assertEqual(a_mano.taxes_id, exento)
        for producto, (lista, variantes) in precios.items():
            self.assertEqual(producto.list_price, lista, 'El precio de la lista no cambia')
            self.assertEqual(producto.product_variant_ids.mapped('lst_price'), variantes)
        self.assertFalse(incluido.active, 'Sin uso: archivado')
        self.assertEqual(self.env['website'].get_current_website().show_line_subtotals_tax_selection, 'tax_excluded')
        self.assertEqual(C.pasar_a_itbms_que_se_suma(self.env), 0, 'Se puede repetir')

    def test_variantes_archivadas_se_pueden_reactivar(self):
        """Archivada, no borrada: conserva su código, su precio y su texto; no sale en la ficha."""
        catalogo = _catalogo(_item('zz-archivo', [
            {'valor': 'CH', 'codigo': 'ZZ-ARC-CH', 'precio': 5.0, 'texto': 'Chica'},
            {'valor': 'GR', 'codigo': 'ZZ-ARC-GR', 'precio': 6.0, 'texto': 'Grande', 'archivada': True},
        ], atributo=ATRIBUTO))
        cargar_catalogo(self.env, catalogo)
        self.assertEqual(C.archivar_variantes(self.env, catalogo).mapped('default_code'), ['ZZ-ARC-GR'])
        grande = self.variante('ZZ-ARC-GR')
        producto = self.producto('zz-archivo')
        self.assertFalse(grande.active)
        self.assertNotIn(grande, producto.product_variant_ids)
        self.assertEqual((grande.lst_price, grande.dcasa_presentacion), (6.0, 'Grande'))
        self.assertNotIn('Grande', [t for _v, t in producto._dcasa_presentaciones()])
        grande.active = True
        self.assertIn(grande, producto.product_variant_ids, 'se reactiva y vuelve con todo')


@tagged('post_install', '-at_install')
class TestCargaDelArchivo(TransactionCase):
    """Las reglas de la carga, con productos de prueba (no los del negocio)."""

    def catalogo(self, *productos, atributos=None):
        return _catalogo(*productos, atributos=atributos)

    def variante(self, codigo):
        return self.env['product.product'].with_context(active_test=False).search([('default_code', '=', codigo)])

    def test_crea_lo_que_falta_con_cada_precio_exacto(self):
        item = _item('zz-tallas', [
            {'valor': 'GR', 'codigo': 'ZZ-GR', 'precio': 12.5, 'existencias': 2, 'texto': 'Grande'},
            {'valor': 'CH', 'codigo': 'ZZ-CH', 'precio': 9.99, 'existencias': None, 'texto': 'Chica'},
        ], atributo=ATRIBUTO, descripcion='Para <probar> el texto')
        self.assertEqual(cargar_catalogo(self.env, self.catalogo(item)), 1)
        producto = self.env.ref(f'dcasa_catalogo.{xmlid_de("zz-tallas")}')
        self.assertEqual(producto.list_price, 9.99)
        self.assertEqual((self.variante('ZZ-GR').lst_price, self.variante('ZZ-CH').lst_price), (12.5, 9.99))
        self.assertEqual(self.variante('ZZ-GR').qty_available, 2)
        self.assertEqual(self.variante('ZZ-CH').qty_available, 0, 'Sin existencias en el archivo: no se ajusta')
        self.assertFalse(self.env['stock.move'].search_count([('product_id', '=', self.variante('ZZ-CH').id)]))
        self.assertEqual(producto.attribute_line_ids.product_template_value_ids.sorted().mapped('name'), ['CH', 'GR'],
                         'El orden del atributo, no el del archivo')
        self.assertIn('Para &lt;probar&gt; el texto', str(producto.description_ecommerce))
        self.assertEqual(cargar_catalogo(self.env, self.catalogo(item)), 0, 'La segunda vez no crea nada')

    def test_vuelve_a_crear_lo_que_falta(self):
        item = _item('zz-simple', [{'codigo': 'ZZ-SIMPLE', 'precio': 7.0, 'existencias': 0, 'texto': 'Uno'}])
        cargar_catalogo(self.env, self.catalogo(item))
        self.env.ref(f'dcasa_catalogo.{xmlid_de("zz-simple")}').unlink()
        self.assertEqual(cargar_catalogo(self.env, self.catalogo(item)), 1)
        self.assertEqual(self.variante('ZZ-SIMPLE').dcasa_presentacion, 'Uno')

    def test_las_fotos_solo_llenan_lo_vacio_y_publican_lo_que_reciben(self):
        # El repositorio no trae fotos: la prueba genera dos JPEG de 8×8 y hace que el catálogo los devuelva.
        fotos = {'prueba-a.jpg': _foto((128, 128, 128)), 'prueba-b.jpg': _foto((200, 200, 200))}
        foto = 'prueba-a.jpg'
        con_variantes = _item('zz-fotos', [
            {'valor': 'CH', 'codigo': 'ZZ-F-CH', 'precio': 5.0, 'existencias': 0, 'foto': foto,
             'fotos_extra': [foto, foto]},
            {'valor': 'GR', 'codigo': 'ZZ-F-GR', 'precio': 6.0, 'existencias': 0},
        ], atributo=ATRIBUTO, foto=foto)
        ya_tenia = _item('zz-ya-tenia', [{'codigo': 'ZZ-YA', 'precio': 7.0, 'existencias': 0}], foto=foto)
        sin_foto = _item('zz-sin-foto', [{'codigo': 'ZZ-SIN-FOTO', 'precio': 8.0, 'existencias': 0}])
        catalogo = self.catalogo(con_variantes, ya_tenia, sin_foto)
        cargar_catalogo(self.env, catalogo)
        with patch.object(C, 'foto_del_catalogo', side_effect=lambda nombre: fotos[nombre]):
            # Una persona ya le puso otra foto a «zz-ya-tenia» y lo dejó sin publicar: se respeta.
            propia = self.env.ref(f'dcasa_catalogo.{xmlid_de("zz-ya-tenia")}')
            propia.image_1920 = fotos['prueba-b.jpg']
            antes = propia.image_1920
            self.assertEqual(C.poner_fotos(self.env, catalogo), 1)
            producto = self.env.ref(f'dcasa_catalogo.{xmlid_de("zz-fotos")}')
            self.assertTrue(producto.image_1920 and producto.is_published)
            self.assertTrue(self.variante('ZZ-F-CH').image_variant_1920)
            self.assertEqual(self.variante('ZZ-F-CH').product_variant_image_ids.mapped('sequence'), [1, 2])
            self.assertFalse(self.variante('ZZ-F-GR').image_variant_1920,
                             'Sin foto de la variante: usa la del producto')
            self.assertEqual(propia.image_1920, antes, 'La foto que puso una persona no se cambia')
            self.assertFalse(propia.is_published, 'ni se publica lo que ella dejó sin publicar')
            sin = self.env.ref(f'dcasa_catalogo.{xmlid_de("zz-sin-foto")}')
            self.assertFalse(sin.image_1920 or sin.is_published)
            # Repetir no duplica nada, ni vuelve a publicar lo que alguien quitó de la web.
            producto.is_published = False
            self.assertEqual(C.poner_fotos(self.env, catalogo), 0)
            self.assertFalse(producto.is_published)
            self.assertEqual(len(self.variante('ZZ-F-CH').product_variant_image_ids), 2)

    def test_publicar_false_pone_la_foto_pero_no_publica(self):
        item = _item('zz-sin-publicar', [{'codigo': 'ZZ-NOPUB', 'precio': 9.0, 'existencias': 0}],
                     foto='prueba-a.jpg', publicar=False)
        catalogo = self.catalogo(item)
        cargar_catalogo(self.env, catalogo)
        with patch.object(C, 'foto_del_catalogo', return_value=_foto((128, 128, 128))):
            self.assertEqual(C.poner_fotos(self.env, catalogo), 0)
        producto = self.env.ref(f'dcasa_catalogo.{xmlid_de("zz-sin-publicar")}')
        self.assertTrue(producto.image_1920)
        self.assertFalse(producto.is_published, 'la activa el dueño')

    def test_foto_del_catalogo_lee_de_data_fotos(self):
        """La función real lee data/fotos/<nombre>: se prueba con un archivo temporal en esa carpeta."""
        carpeta = os.path.join(get_module_path('dcasa_catalogo'), 'data', 'fotos')
        creada = not os.path.isdir(carpeta)
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, 'zz-prueba-temporal.jpg')
        try:
            contenido = _foto((90, 90, 90))
            with open(ruta, 'wb') as archivo:
                archivo.write(base64.b64decode(contenido))
            self.assertEqual(C.foto_del_catalogo('zz-prueba-temporal.jpg'), contenido)
        finally:
            if os.path.exists(ruta):
                os.remove(ruta)
            if creada:
                os.rmdir(carpeta)

    def test_un_precio_que_falta_no_se_inventa(self):
        item = _item('zz-sin-precio', [{'codigo': 'ZZ-SIN-PRECIO', 'precio': None, 'existencias': 3}])
        with self.assertLogs('odoo.addons.dcasa_catalogo.catalogo', 'WARNING') as registro:
            self.assertEqual(cargar_catalogo(self.env, self.catalogo(item)), 0)
        self.assertIn('el precio no se inventa', '\n'.join(registro.output))
        self.assertFalse(self.variante('ZZ-SIN-PRECIO'))

    def test_un_codigo_que_ya_esta_en_odoo_no_se_duplica(self):
        """Si alguien (o Brian, con el Excel de un proveedor) ya creó el código, la carga no lo duplica ni lo pisa."""
        a_mano = self.env['product.template'].create({'name': 'Hecho a mano', 'default_code': 'ZZ-MANO'})
        item = _item('zz-mano', [{'codigo': 'ZZ-MANO', 'precio': 5.0, 'existencias': 1}])
        with self.assertLogs('odoo.addons.dcasa_catalogo.catalogo', 'WARNING'):
            self.assertEqual(cargar_catalogo(self.env, self.catalogo(item)), 0)
        self.assertEqual(self.variante('ZZ-MANO'), a_mano.product_variant_id)

    def test_la_categoria_sale_del_nombre_como_en_la_importacion_de_brian(self):
        """``reglas.CATEGORIAS`` está vacío (Tommalo usa la categoría de su proveedor): sin regla no hay categoría.
        Con una regla agregada, la categoría sale del nombre y los valores de un producto nuevo la llevan: lo mismo
        que usan el inventario anterior y la importación del Excel de un proveedor con Brian."""
        impuesto = self.env.ref('base.main_company').account_sale_tax_id
        self.assertEqual(reglas.CATEGORIAS, [])
        self.assertIsNone(categoria_de_nombre('Crema de prueba'), 'Sin coincidencia: None')
        self.assertEqual(categoria_de_nombre('Crema de prueba', 'otro'), 'otro', 'o el valor por defecto')
        self.assertNotIn('categ_id', C.valores_producto_nuevo(self.env, 'Crema de prueba', 1.0, impuesto, None))
        reglas_de_prueba = [(r'\bcrema\b', 'belleza'), (r'l[aá]mpara', 'hogar'), (r'vitamina', 'salud')]
        with patch.object(reglas, 'CATEGORIAS', reglas_de_prueba):
            for nombre, clave in (('Crema de prueba', 'belleza'), ('Lámpara de prueba', 'hogar'),
                                  ('Vitaminas de prueba', 'salud')):
                self.assertEqual(categoria_de_nombre(nombre), clave, nombre)
                vals = C.valores_producto_nuevo(self.env, nombre, 10.0, impuesto, categoria_de_nombre(nombre))
                self.assertEqual(vals['categ_id'], self.env.ref(f'dcasa_catalogo.product_category_{clave}').id,
                                 nombre)
                self.assertEqual(vals['public_categ_ids'],
                                 [(6, 0, self.env.ref(f'website_dcasa.public_category_{clave}').ids)], nombre)
            self.assertIsNone(categoria_de_nombre('Artículo sin regla'))
        self.assertIsNone(categoria_de_nombre('Crema de prueba'), 'Al salir de la prueba, vuelve a estar vacío')

    def test_un_archivo_mal_escrito_detiene_la_carga(self):
        malos = [
            _item('zz-1', [{'valor': 'XS', 'codigo': 'ZZ-XS', 'precio': 1.0}], atributo=ATRIBUTO),
            _item('zz-2', [{'valor': 'CH', 'codigo': 'ZZ-A', 'precio': 1.0}], atributo='Color que no está'),
            _item('zz-3', [{'codigo': 'ZZ-B', 'precio': 1.0}, {'codigo': 'ZZ-C', 'precio': 2.0}]),
            _item('zz-4', [{'codigo': 'ZZ-D', 'precio': 1.0}], categoria='categoria-que-no-existe'),
            _item('zz-5', [{'valor': 'CH', 'codigo': 'ZZ-E', 'precio': 1.0},
                           {'valor': 'MED', 'codigo': 'ZZ-E', 'precio': 1.0}], atributo=ATRIBUTO),
        ]
        for item in malos:
            with self.subTest(item['clave']), self.assertRaises(ValueError):
                cargar_catalogo(self.env, self.catalogo(item))
        self.assertFalse(self.variante('ZZ-B') | self.variante('ZZ-D'), 'No se creó nada a medias')


@tagged('post_install', '-at_install')
class TestFichaConPresentacion(HttpCase):
    """La ficha de la tienda muestra la presentación de cada variante (unidades y medidas), aparte del precio."""

    def test_la_ficha_dice_la_presentacion_de_cada_variante(self):
        textos = {'ZZ-FICHA-CH': 'Frasco chico de prueba — 50 ml', 'ZZ-FICHA-GR': 'Frasco grande de prueba — 120 ml'}
        catalogo = _catalogo(_item('zz-ficha', [
            {'valor': 'CH', 'codigo': 'ZZ-FICHA-CH', 'precio': 9.99, 'existencias': 3, 'texto': textos['ZZ-FICHA-CH']},
            {'valor': 'GR', 'codigo': 'ZZ-FICHA-GR', 'precio': 12.5, 'existencias': 3,
             'texto': textos['ZZ-FICHA-GR']},
        ], atributo=ATRIBUTO))
        cargar_catalogo(self.env, catalogo)
        producto = self.env.ref(f'dcasa_catalogo.{xmlid_de("zz-ficha")}')
        producto.is_published = True
        html = self.url_open(producto.website_url).text
        self.assertIn('<dt>Presentación</dt>', html)
        for texto in textos.values():
            self.assertIn(texto, html)


@tagged('post_install', '-at_install')
class TestBuscarProductos(TransactionCase):

    def test_filtros_rapidos_y_categorias(self):
        vista = self.env['product.template'].get_view(
            self.env.ref('product.product_template_search_view').id, 'search')
        arch = vista['arch']
        for nombre in ('dcasa_disponibles', 'dcasa_pocas', 'dcasa_agotados', 'dcasa_precio_1', 'dcasa_precio_4',
                       'dcasa_en_web'):
            self.assertIn(f'name="{nombre}"', arch)
        self.assertIn('<searchpanel', arch)
        self.assertIn('public_categ_ids', arch)
        # Los dominios funcionan de verdad (campos buscables).
        Producto = self.env['product.template']
        barato = Producto.create({'name': 'Crema de prueba', 'list_price': 50, 'is_storable': True})
        caro = Producto.create({'name': 'Lámpara de prueba', 'list_price': 900, 'is_storable': True})
        self.assertIn(barato, Producto.search([('list_price', '<=', 100)]))
        self.assertNotIn(caro, Producto.search([('list_price', '<=', 100)]))
        self.assertIn(caro, Producto.search([('is_storable', '=', True), ('qty_available', '<=', 0)]))
