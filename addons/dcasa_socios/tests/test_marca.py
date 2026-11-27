"""Socios con la marca Tommalo (docs/MARCA_TOMMALO.md): la placa de puntos en verde salvia con todo en navy,
el botón principal naranja con letra navy, Montserrat, y el nombre de la tienda en lugar de «D'CASA». El panel de
Ajustes de vendedores, con el filo naranja y el navy."""
import re
from pathlib import Path

from PIL import Image

from odoo.tests import HttpCase, tagged

from ..models.bien_escrito import mensaje_del_correo
from ..models.res_partner_vend import TIPOS_VENDEDOR

MODULO = Path(__file__).resolve().parents[1]
# Lo de D'CASA que no puede quedar en las hojas de estilo (docs/MARCA_TOMMALO.md › De D'CASA a Tommalo).
DE_DCASA = re.compile(r'#1340B1|#FED00F|#0E2A6B|#0F3591|#0B2A6F|#0B2160|rgba?\(\s*19,\s*64,\s*177|\bAnton\b'
                      r'|\bOswald\b|\bInter\b', re.I)
# El naranja y el verde de Tommalo son RELLENO (2.20 y 1.75 sobre el crema): nunca color de letra, borde ni aro.
RELLENO_COMO_LETRA = re.compile(r'(?<![-\w])(?:color|border(?:-[a-z]+)*|outline(?:-color)?)\s*:[^;{]*'
                                r'(?:#D4D4D4|#BDBDBD|var\(--o-dcbt-(?:accent|sage)\)|var\(--dcc-acento\)'
                                r'|\$[a-z]+-(?:accent|sage)\b(?!-))', re.I)


def sin_comentarios(scss):
    return re.sub(r'//[^\n]*', '', re.sub(r'/\*.*?\*/', '', scss, flags=re.S))


def revisar_hoja(caso, ruta, de_tommalo=('#D4D4D4', '#262626', 'Montserrat')):
    """La hoja no trae nada de D'CASA, sí los colores y la letra de Tommalo, y no usa el relleno como letra."""
    texto = sin_comentarios((MODULO / ruta).read_text(encoding='utf-8'))
    caso.assertEqual(DE_DCASA.findall(texto), [], f'{ruta}: queda la marca de D’CASA')
    for valor in de_tommalo:
        caso.assertIn(valor.lower(), texto.lower(), f'{ruta}: falta {valor} de la marca Tommalo')
    caso.assertEqual(RELLENO_COMO_LETRA.findall(texto), [], f'{ruta}: el naranja o el verde como letra o borde')


@tagged('post_install', '-at_install')
class TestMarcaSocios(HttpCase):

    def test_las_hojas_de_socios_y_de_ajustes_de_vendedores(self):
        revisar_hoja(self, 'static/src/scss/socios.scss', ('#D4D4D4', '#262626', '#BDBDBD', 'Montserrat'))
        revisar_hoja(self, 'static/src/scss/vendedores_ajustes.scss', ('#8A8A8A', '#262626'))

    def test_socios_dice_tus_puntos_con_el_nombre_de_la_tienda(self):
        html = self.url_open('/socios').text
        self.assertIn('Tus puntos', html, 'lo mira el CI')
        self.assertIn('Tus puntos Tommalo', html)
        for de_origen in ("Tus puntos D'CASA", 'Tus puntos D&#39;CASA', 'Socios D’CASA', "compraste en D'CASA"):
            self.assertNotIn(de_origen, html)

    def test_el_nombre_del_modulo_no_es_el_de_la_plantilla_de_origen(self):
        modulo = self.env['ir.module.module'].search([('name', '=', MODULO.name)])
        self.assertTrue(modulo.shortdesc.startswith('Tommalo — '), modulo.shortdesc)
        self.assertNotIn("D'CASA", modulo.shortdesc + (modulo.summary or ''))

    def test_nada_de_lo_que_se_ve_dice_d_casa(self):
        """El nombre de la empresa donde el texto se arma en el código; «Tommalo» en las etiquetas fijas."""
        empresa = self.env.company.name
        self.assertEqual(dict(TIPOS_VENDEDOR)['empleado'], 'Empleado de Tommalo')
        self.assertEqual(self.env.ref('dcasa_socios.product_premio_canje').name,
                         'Premio del programa Socios Tommalo')
        self.assertEqual(self.env.ref('dcasa_socios.ir_cron_programa_socios').name,
                         'Socios: vencer canjes y regalos de cumpleaños')
        self.assertTrue(self.env['dcasa.premio']._fields['costo'].help.startswith(
            'Lo que de verdad le cuesta a la tienda.'))
        self.assertEqual(mensaje_del_correo(self.env, 'ventas@ejemplo.com', 'equipo'),
                         f'Ese correo es de {empresa} o de alguien del equipo: escribe el del cliente.')
        for vista, pestana in (('dcasa_socios.view_partner_form_dcasa_socios', 'Socio Tommalo'),
                               ('dcasa_socios.view_partner_form_dcasa_vendedores', 'Vendedor Tommalo')):
            arco = self.env.ref(vista).arch
            self.assertIn(f'string="{pestana}"', arco)
            self.assertNotIn("D'CASA", arco)

    def test_el_icono_del_modulo_con_los_colores_de_la_marca(self):
        icono = Image.open(MODULO / 'static/description/icon.png').convert('RGB')
        colores = {color for _n, color in icono.getcolors(2 ** 20)}
        self.assertIn((38, 38, 38), colores, 'el navy')
        self.assertIn((212, 212, 212), colores, 'el naranja')
        self.assertFalse(colores & {(19, 64, 177), (254, 208, 15)}, 'ni el azul ni el amarillo de D’CASA')
