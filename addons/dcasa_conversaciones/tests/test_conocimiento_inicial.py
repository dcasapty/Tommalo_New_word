"""El conocimiento inicial de Tommalo (conocimiento_inicial/tommalo.json): se siembra una vez por ficha.

El archivo de Tommalo está sin fichas (PENDIENTE: el cliente aún no decide su conocimiento); aquí se prueba el
mecanismo con fichas genéricas inventadas. El archivo solo siembra: lo que se cambie en el panel no se pisa, lo que se
borre no vuelve, y una instalación sin ``DCASA_CONOCIMIENTO_INICIAL`` sigue en cero (test_conocimiento.py)."""
import copy

from odoo.tests import TransactionCase, tagged

from ..conocimiento_inicial import PARAM_CARGADAS, cargar_conocimiento_inicial, leer_conocimiento_inicial
from ..models.conocimiento import MAX_CONTENIDO
from .test_conocimiento_en_cero import HECHOS_DE_DCASA

# Fichas inventadas para probar el mecanismo (no son conocimiento de ningún negocio).
DATOS_DE_PRUEBA = {
    'fuente': 'Datos de prueba',
    'entradas': [
        {'clave': 'horario-de-prueba', 'titulo': 'Horario de prueba',
         'contenido': 'Se atiende de lunes a viernes. Dato de prueba.', 'etiquetas': ['horario', 'prueba']},
        {'clave': 'regalo-de-prueba', 'titulo': 'Regalo de prueba',
         'contenido': 'Sí se puede envolver para regalo. Dato de prueba.', 'etiquetas': ['regalo', 'envoltura']},
        {'clave': 'pagos-de-prueba', 'titulo': 'Formas de pago de prueba',
         'contenido': 'Se acepta Yappy y tarjeta. Dato de prueba.', 'etiquetas': ['pago', 'yappy', 'tarjeta']},
        {'clave': 'apagada-de-prueba', 'titulo': 'Ficha apagada de prueba',
         'contenido': 'Esta ficha nace apagada. Dato de prueba.', 'etiquetas': ['apagada'], 'activo': False,
         'nota': 'Apagado por decisión del dueño (prueba).'},
    ],
}


@tagged('post_install', '-at_install')
class TestConocimientoInicial(TransactionCase):

    def setUp(self):
        super().setUp()
        self.datos = copy.deepcopy(DATOS_DE_PRUEBA)
        self.Conocimiento = self.env['dcasa.conocimiento'].with_context(active_test=False)

    def test_el_archivo_es_de_tommalo_y_cabe(self):
        real = leer_conocimiento_inicial('tommalo')
        self.assertIn('fuente', real)
        self.assertIsInstance(real['entradas'], list)
        claves = [e['clave'] for e in real['entradas']]
        self.assertEqual(len(claves), len(set(claves)), 'cada clave una sola vez')
        for entrada in real['entradas'] + self.datos['entradas']:
            with self.subTest(entrada['clave']):
                texto = f"{entrada['titulo']} {entrada['contenido']} {' '.join(entrada.get('etiquetas') or [])}"
                self.assertFalse([m.group(0) for m in HECHOS_DE_DCASA.finditer(texto)], 'nada de otro negocio')
                self.assertLessEqual(len(entrada['contenido']), MAX_CONTENIDO)

    def test_el_archivo_carga_sin_error(self):
        """Con cero fichas, cargar no crea nada y no falla (el arranque lo corre con DCASA_CONOCIMIENTO_INICIAL)."""
        real = leer_conocimiento_inicial('tommalo')
        creadas = cargar_conocimiento_inicial(self.env, 'tommalo')
        self.assertEqual(len(creadas), len(real['entradas']))

    def test_siembra_una_vez_y_respeta_el_panel(self):
        creadas = cargar_conocimiento_inicial(self.env, 'tommalo', self.datos)
        self.assertEqual(len(creadas), len(self.datos['entradas']))
        self.assertTrue(all(c.fuente == 'manual' for c in creadas), 'fichas normales del panel')
        apagada = creadas.filtered(lambda c: c.titulo.startswith('Ficha apagada'))
        self.assertFalse(apagada.activo, 'una ficha marcada activo=false nace apagada')
        self.assertIn('Apagado por decisión del dueño', apagada.nota)
        self.assertEqual(len(creadas.filtered('activo')), len(creadas) - 1)
        # La segunda vez no crea nada.
        self.assertFalse(cargar_conocimiento_inicial(self.env, 'tommalo', self.datos))
        # Lo que cambia el equipo en el panel no se pisa, y lo que borra no vuelve.
        horario = creadas.filtered(lambda c: c.titulo == 'Horario de prueba')
        horario.contenido = 'Texto corregido en el panel'
        regalo = creadas.filtered(lambda c: c.titulo == 'Regalo de prueba')
        regalo.unlink()
        self.assertFalse(cargar_conocimiento_inicial(self.env, 'tommalo', self.datos))
        self.assertEqual(horario.contenido, 'Texto corregido en el panel')
        self.assertFalse(self.Conocimiento.search([('titulo', '=', 'Regalo de prueba')]))
        self.assertIn('tommalo:horario-de-prueba',
                      self.env['ir.config_parameter'].sudo().get_param(PARAM_CARGADAS))

    def test_una_ficha_nueva_en_el_archivo_se_crea_en_el_siguiente_arranque(self):
        cargar_conocimiento_inicial(self.env, 'tommalo', self.datos)
        datos = copy.deepcopy(self.datos)
        datos['entradas'].append({'clave': 'nueva-de-prueba', 'titulo': 'Ficha nueva de prueba',
                                  'contenido': 'Una ficha que se agregó después.', 'etiquetas': ['prueba']})
        self.assertEqual(cargar_conocimiento_inicial(self.env, 'tommalo', datos).titulo, 'Ficha nueva de prueba')

    def test_el_asistente_la_encuentra(self):
        cargar_conocimiento_inicial(self.env, 'tommalo', self.datos)
        Conocimiento = self.env['dcasa.conocimiento']
        for pregunta, titulo in (('¿cuál es el horario de atención?', 'Horario de prueba'),
                                 ('¿aceptan yappy?', 'Formas de pago de prueba')):
            with self.subTest(pregunta):
                titulos = [e.titulo for e, _puntos in Conocimiento._buscar(pregunta, 3)]
                self.assertIn(titulo, titulos)
        self.assertNotIn('Ficha apagada de prueba',
                         [e.titulo for e, _puntos in Conocimiento._buscar('ficha apagada', 3)],
                         'lo apagado no lo ve el asistente')

    def test_un_negocio_sin_archivo(self):
        with self.assertRaises(ValueError):
            leer_conocimiento_inicial('otro_negocio')
