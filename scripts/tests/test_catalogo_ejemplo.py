"""El catálogo de EJEMPLO (scripts/ejemplo_catalogo_tommalo.json) tiene el formato de la carga y es claramente de prueba."""
import json
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CATEGORIAS = {'belleza', 'hogar', 'salud', 'otro'}


class TestCatalogoEjemplo(unittest.TestCase):
    def setUp(self):
        self.catalogo = json.loads((RAIZ / 'scripts/ejemplo_catalogo_tommalo.json').read_text(encoding='utf-8'))

    def test_formato_de_la_carga(self):
        self.assertEqual(set(self.catalogo), {'fuente', 'atributos', 'productos'})
        claves, codigos = set(), set()
        for producto in self.catalogo['productos']:
            self.assertIn(producto['categoria'], CATEGORIAS)
            self.assertNotIn(producto['clave'], claves)
            claves.add(producto['clave'])
            for variante in producto['variantes']:
                self.assertNotIn(variante['codigo'], codigos)
                codigos.add(variante['codigo'])
                self.assertIsInstance(variante['precio'], (int, float))
                if producto.get('atributo'):
                    self.assertIn(variante['valor'], self.catalogo['atributos'][producto['atributo']])

    def test_todo_dice_que_es_de_prueba(self):
        self.assertIn('EJEMPLO', self.catalogo['fuente'])
        for producto in self.catalogo['productos']:
            self.assertIn('(de prueba)', producto['nombre'])
            self.assertTrue(producto['clave'].startswith('ejemplo-'))
            for variante in producto['variantes']:
                self.assertTrue(variante['codigo'].startswith('EJ-'), 'los códigos de ejemplo empiezan por EJ-')

    def test_sin_fotos_ni_datos_de_proveedor(self):
        texto = json.dumps(self.catalogo, ensure_ascii=False).lower()
        for prohibido in ('foto', 'dropi', 'costo', '@', 'http'):
            self.assertNotIn(prohibido, texto)


if __name__ == '__main__':
    unittest.main()
