"""Sin efecto en Tommalo: en el negocio de origen esta versión archivó una variante y apagó la venta de lo agotado
en los productos ya creados.

Tommalo parte de un catálogo vacío; ``no_vender_agotados`` ya corre al instalar (``__init__.py``) y
``archivar_variantes`` solo actúa sobre lo marcado en ``data/catalogo.json``. El archivo se conserva para que la
versión siga en la cadena de migraciones.
"""


def migrate(cr, version):
    return
