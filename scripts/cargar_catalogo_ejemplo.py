# ruff: noqa: F821  (`env` lo inyecta `odoo-bin shell`)
"""Carga un catálogo de EJEMPLO (inventado, marcado «de prueba») para ensayar la tienda de Tommalo.

NO es el catálogo de Tommalo: sus productos, precios y existencias no existen. Sirve para ver cómo se ve la tienda con
productos, probar el carrito y las pruebas a mano. El catálogo real se incorporará después (módulo
``dcasa_catalogo_tommalo``, docs/CATALOGO.md).

Uso (en una base de pruebas, NUNCA en producción)::

    odoo-bin shell -d <base> --addons-path=... < scripts/cargar_catalogo_ejemplo.py

Se niega a correr si ``DCASA_ENTORNO`` es «produccion» o si la base ya tiene productos que no son de ejemplo. Es
idempotente: una segunda corrida no duplica nada. Usa la misma carga que el catálogo de verdad
(``dcasa_catalogo.catalogo.cargar_catalogo``), así que además comprueba que la carga funciona.
"""
import json
import os

from odoo.addons.dcasa_catalogo.catalogo import cargar_catalogo

if os.environ.get('DCASA_ENTORNO') == 'produccion':
    raise SystemExit('✖ Esto es un catálogo de EJEMPLO: no se carga en producción.')

# Se corre desde la raíz del repositorio (como scripts/integracion_juan.sh).
ruta = os.path.join(os.getcwd(), 'scripts', 'ejemplo_catalogo_tommalo.json')
with open(ruta, encoding='utf-8') as archivo:
    catalogo = json.load(archivo)

ajenos = env['product.template'].with_context(active_test=False).search(
    [('default_code', '!=', False), '!', ('default_code', '=like', 'EJ-%')], limit=1)
if ajenos:
    raise SystemExit('✖ La base ya tiene productos que no son de ejemplo: no se mezcla el ejemplo con datos reales.')

creados = cargar_catalogo(env, catalogo)
env.cr.commit()
print(f'Catálogo de ejemplo: {creados} productos nuevos (de prueba).')
