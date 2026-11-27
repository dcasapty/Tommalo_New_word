"""Páginas legales: existen, están enlazadas en el pie y dicen lo que el sistema hace de verdad.

Texto provisional (lo revisa la asesoría legal de Tommalo): conserva la estructura y dice PENDIENTE, a la vista, en lo
que Tommalo todavía no dio (RUC, dirección, correo, proveedor de inteligencia artificial)."""
from odoo.tests import HttpCase, tagged

EMPRESA = 'Tommalo, RUC PENDIENTE, dirección PENDIENTE.'
# Lo de la tienda de origen que no puede quedar en ninguna de las dos páginas.
DE_LA_TIENDA_DE_ORIGEN = ("D'CASA", 'D&#39;CASA', 'La Chorrera', 'dcasapty')


@tagged('post_install', '-at_install')
class TestPaginasLegales(HttpCase):

    def test_privacidad(self):
        respuesta = self.url_open('/privacidad')
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.text
        self.assertIn('Política de privacidad', html)
        self.assertIn(EMPRESA, html)
        self.assertIn('Correo: PENDIENTE.', html)
        self.assertNotIn('mailto:', html, 'sin correo inventado')
        self.assertIn('Ley 81 de 2019', html)
        # Socios, con el nombre de la empresa; el proveedor de IA lo decide Tommalo (PENDIENTE), no el de otro negocio.
        self.assertIn('Si eres Socio Tommalo', html)
        self.assertIn('nadie en Tommalo puede leerlo', html)
        self.assertIn('del programa Socios Tommalo', html)
        self.assertIn('PENDIENTE (lo decide Tommalo)', html)
        self.assertNotIn('Anthropic</strong>', html)
        self.assertNotIn('Muse Spark', html)
        # El nombre de la plantilla sale en og:title: sin la marca de otra empresa.
        self.assertIn('<meta property="og:title" content="Página legal | Tommalo"/>', html)
        for dato in DE_LA_TIENDA_DE_ORIGEN:
            self.assertNotIn(dato, html)
        # El uso de IA está dicho en claro; qué proveedor y si entrena sus modelos lo decide Tommalo (PENDIENTE).
        self.assertIn('id="inteligencia-artificial"', html)
        self.assertNotIn('Meta puede usar ese contenido para entrenar', html)
        # Juan (el asistente que contesta a los clientes) está nombrado: es comportamiento real del sistema.
        self.assertIn('te contesta primero <strong>Juan</strong>', html)
        self.assertRegex(html, r'notas de voz\s+y lee las fotos')
        self.assertIn('id="cookies"', html)

    def test_terminos(self):
        respuesta = self.url_open('/terminos')
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.text
        self.assertIn('Términos y condiciones', html)
        self.assertIn(f'Este sitio es de {EMPRESA}', html)
        self.assertIn('Programa Socios Tommalo', html)
        self.assertIn('una persona de Tommalo, vale lo que te confirmó la persona', html)
        self.assertIn('no incluyen el ITBMS', html)
        for dato in DE_LA_TIENDA_DE_ORIGEN:
            self.assertNotIn(dato, html)
        self.assertIn('href="/privacidad#inteligencia-artificial"', html)
        self.assertIn('href="/socios/terminos"', html)

    def test_pie_enlaza_paginas_legales_sin_ruc_inventado(self):
        """El pie enlaza las dos páginas. El RUC de Tommalo todavía no está: el pie no muestra ninguno."""
        html = self.url_open('/').text
        self.assertIn('href="/privacidad"', html)
        self.assertIn('href="/terminos"', html)
        self.assertNotIn('RUC ', html.split('id="footer"', 1)[-1].split('</footer>', 1)[0])
