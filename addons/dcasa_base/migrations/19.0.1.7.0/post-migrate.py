"""Sin efecto en Tommalo.

En el negocio de origen esta migración ponía la dirección real de la tienda. Tommalo no tiene dirección todavía
(PENDIENTE: se escribe en Ajustes › Empresas) y nunca se copia la de otro negocio. Se deja el archivo para que la versión
19.0.1.7.0 siga existiendo en la cadena de migraciones.
"""


def migrate(cr, version):
    return
