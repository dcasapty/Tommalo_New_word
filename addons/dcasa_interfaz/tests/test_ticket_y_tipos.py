"""Ticket promedio y unidades vendidas por tipo en el Inicio de Gerencia (K1, docs/DECISIONES_CONTABLES.md, 2026-10-18).

Siguen la base del interruptor, el periodo y la vendedora (las mismas facturas de ``_medir``); las notas de crédito
restan. Fechas de 2025 y casi todo con filtro de vendedora, para no mezclarse con otras pruebas.
"""
from datetime import date, datetime

from odoo import Command
from odoo.tests import tagged

from .test_facturado import FacturadoCommon


@tagged('post_install', '-at_install')
class TestTicketYTipos(FacturadoCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Categoria = cls.env['product.category']
        estantes = Categoria.create({'name': 'Estantes K1'})
        salas = Categoria.create({'name': 'Salas K1', 'parent_id': estantes.id})
        recamaras = Categoria.create({'name': 'Recámaras K1', 'parent_id': estantes.id})
        lamparas = Categoria.create({'name': 'Lámparas K1',
            'parent_id': recamaras.id})  # más abajo: cuenta en Recámaras
        jabones = Categoria.create({'name': 'Jabones K1'})                        # raíz: es su propio tipo
        cls.espejo = cls.nuevo_producto('Espejo K1', salas, 800.0)
        cls.lampara_k1 = cls.nuevo_producto('Lámpara K1', lamparas, 500.0)
        cls.jabon = cls.nuevo_producto('Jabón K1', jabones, 300.0)

    @classmethod
    def nuevo_producto(cls, nombre, categoria, precio):
        return cls.env['product.product'].create({
            'name': nombre, 'categ_id': categoria.id, 'list_price': precio, 'standard_price': precio / 2,
            'taxes_id': [Command.clear()]})

    def linea(self, producto, cantidad=1):
        return Command.create({'product_id': producto.id, 'quantity': cantidad, 'price_unit': producto.list_price})

    def tarjeta(self, dia, **kw):
        return self.tablero.with_user(self.gerencia).ventas_del_periodo('rango', str(dia), str(dia), **kw)

    def test_ticket_promedio_con_y_sin_ventas(self):
        a, b = date(2025, 3, 10), date(2025, 3, 3)
        self.suelta(b, self.espejo, vendedor=self.otra)                                  # B: una de $800
        self.suelta(a, self.espejo, vendedor=self.otra)
        lampara = self.suelta(a, self.lampara_k1, cantidad=2, vendedor=self.otra)
        self.nota(lampara, a, precio=500.0)                     # resta del monto, no del número de ventas
        actual = self.tarjeta(a, vendedor=self.otra.id)['actual']
        self.assertEqual((actual['sin_itbms'], actual['cuantas'], actual['notas']), (1300.0, 2, 1))
        self.assertEqual(actual['ticket'], 650.0)
        filas = self.filas(self.comparar('semana_pasada', datetime(2025, 3, 10, 18, 0), vendedor=self.otra.id))
        self.assertEqual([clave for clave in filas], ['ventas', 'ganancia', 'margen', 'cuantas', 'ticket', 'cobrado'])
        self.assertEqual((filas['ticket']['a'], filas['ticket']['b'], filas['ticket']['formato']),
                         (650.0, 800.0, 'moneda'))
        self.assertEqual(filas['ticket']['cambio'], {'tipo': 'pct', 'valor': -18.8, 'sentido': 'baja',
                                                     'invertido': False})
        # Sin ventas: «—» (None), sin dividir entre cero, en la tarjeta y en Comparar.
        self.assertIsNone(self.tarjeta(date(2025, 3, 11), vendedor=self.otra.id)['actual']['ticket'])
        vacio = self.filas(self.comparar('ayer', datetime(2025, 3, 11, 18, 0), vendedor=self.otra.id))['ticket']
        self.assertEqual((vacio['a'], vacio['b'], vacio['cambio']['valor']), (None, 650.0, None))
        # En «Mes» la última columna es «Llevas»: de un promedio no dice nada.
        mes = self.filas(self.comparar('mes', datetime(2025, 4, 5, 10, 0), mes='2025-03', vendedor=self.otra.id))
        self.assertEqual((mes['ticket']['b'], mes['ticket']['cambio']['valor']), (700.0, None), '$2,100 ÷ 3')

    def test_unidades_por_tipo_con_una_nota_de_credito_que_resta(self):
        dia = date(2025, 3, 12)
        self.suelta(dia, vendedor=self.otra, lineas=[
            self.linea(self.espejo), self.linea(self.flete),                             # el flete es servicio: fuera
            Command.create({'name': 'Descuento', 'quantity': 1, 'price_unit': -50.0})])  # sin producto: fuera
        lampara = self.suelta(dia, vendedor=self.otra,
                              lineas=[self.linea(self.lampara_k1, 2), self.linea(self.jabon, 3)])
        nota = self.nota(lampara, dia, precio=500.0)          # devuelve 1 lámpara (su primera línea)
        self.assertEqual(nota.invoice_line_ids.product_id, self.lampara_k1)
        unidades = self.tarjeta(dia, vendedor=self.otra.id)['unidades']
        self.assertEqual(unidades['tipos'], [{'tipo': 'Jabones K1', 'unidades': 3.0},
                                             {'tipo': 'Recámaras K1', 'unidades': 1.0},
                                             {'tipo': 'Salas K1', 'unidades': 1.0}])
        self.assertEqual(unidades['total'], 5.0)

    def test_sigue_la_base_y_la_vendedora(self):
        dia = date(2025, 3, 13)
        self.suelta(dia, self.espejo, vendedor=self.vendedora)                           # sin pagar
        pagada = self.suelta(dia, self.lampara_k1, vendedor=self.vendedora)
        self.pagar(pagada, 500.0, dia)
        self.suelta(dia, self.jabon, cantidad=2, vendedor=self.otra)
        ana = self.tarjeta(dia, vendedor=self.vendedora.id)
        self.assertEqual(ana['actual']['ticket'], 650.0)
        self.assertEqual(ana['unidades']['tipos'], [{'tipo': 'Recámaras K1', 'unidades': 1.0},
                                                    {'tipo': 'Salas K1', 'unidades': 1.0}])
        completadas = self.tarjeta(dia, vendedor=self.vendedora.id, base='completadas')
        self.assertEqual(completadas['actual']['ticket'], 500.0)
        self.assertEqual(completadas['unidades'], {'tipos': [{'tipo': 'Recámaras K1', 'unidades': 1.0}], 'total': 1.0})
        otra = self.tarjeta(dia, vendedor=self.otra.id)
        self.assertEqual((otra['actual']['ticket'], otra['unidades']['total']), (600.0, 2.0))
        cmp = self.filas(self.comparar('ayer', datetime(2025, 3, 13, 18, 0), vendedor=self.vendedora.id,
                                       base='completadas'))
        self.assertEqual(cmp['ticket']['a'], 500.0, 'Comparar usa la misma base y la misma vendedora')
        # La vendedora (panel propio) no recibe las unidades por tipo: son del Inicio de Gerencia.
        self.assertIsNone(self.tablero.with_user(self.vendedora).ventas_del_periodo(
            'rango', str(dia), str(dia))['unidades'])

    def test_pasados_ocho_tipos_los_demas_van_en_otros(self):
        dia = date(2025, 3, 14)
        lineas = []
        for numero in range(1, 11):                          # 10 tipos: el tipo N vende N unidades
            categoria = self.env['product.category'].create({'name': f'Tipo K1 {numero:02d}'})
            lineas.append(self.linea(self.nuevo_producto(f'Producto K1 {numero}', categoria, 10.0), numero))
        self.suelta(dia, vendedor=self.otra, lineas=lineas)
        unidades = self.tarjeta(dia, vendedor=self.otra.id)['unidades']
        self.assertEqual([fila['tipo'] for fila in unidades['tipos']],
                         [f'Tipo K1 {numero:02d}' for numero in range(10, 2, -1)] + ['Otros'])
        self.assertEqual(unidades['tipos'][-1]['unidades'], 3.0, 'los tipos 2 y 1')
        self.assertEqual(unidades['total'], 55.0)
