"""Sin efecto en Tommalo: en el negocio de origen esta versión puso las fotos del catálogo en productos ya creados.

Tommalo parte de un catálogo vacío (sin fotos en ``data/fotos/``). El archivo se conserva para que la versión siga en
la cadena de migraciones.
"""


def migrate(cr, version):
    return
