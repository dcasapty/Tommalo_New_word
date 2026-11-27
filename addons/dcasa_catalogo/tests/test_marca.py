"""El catálogo con la marca Tommalo (docs/MARCA_TOMMALO.md): en la ficha, las insignias de disponibilidad y la
caja de medidas; en el panel, «Armar combo» (con los tokens del panel y el valor de Tommalo de respaldo)."""
import re
from pathlib import Path

from odoo.tests import TransactionCase, tagged

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
class TestMarcaCatalogo(TransactionCase):

    def test_la_hoja_de_la_ficha(self):
        revisar_hoja(self, 'static/src/scss/catalogo.scss', ('#D4D4D4', '#262626', '#BDBDBD', 'Montserrat'))

    def test_armar_combo_sigue_los_tokens_del_panel_con_la_marca_de_respaldo(self):
        revisar_hoja(self, 'static/src/combo/armar_combo.scss')
        texto = sin_comentarios((MODULO / 'static/src/combo/armar_combo.scss').read_text(encoding='utf-8'))
        self.assertIn('var(--dc-naranja, #D4D4D4)', texto, 'el naranja del panel (Ajustes › Marca del panel)')
        self.assertNotIn('--dc-azul', texto, 'ya no lee la escala azul de D’CASA')

    def test_el_nombre_del_modulo_no_es_el_de_la_plantilla_de_origen(self):
        modulo = self.env['ir.module.module'].search([('name', '=', MODULO.name)])
        self.assertTrue(modulo.shortdesc.startswith('Tommalo — '), modulo.shortdesc)
        self.assertNotIn("D'CASA", modulo.shortdesc + (modulo.summary or ''))
