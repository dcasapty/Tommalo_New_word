"""Sin efecto en Tommalo: en el negocio de origen esta versión cargó un «Precio por par» (promoción «2 por…») a una
variante ya creada.

El mecanismo (``models/precio_par.py``) se queda; Tommalo no trae precios por par cargados. El archivo se conserva
para que la versión siga en la cadena de migraciones.
"""


def migrate(cr, version):
    return
