"""Sin efecto en Tommalo.

En el negocio de origen esta migración cambiaba datos de la empresa (colores o razón social) de una base ya instalada.
Tommalo empieza con su base vacía y esos valores salen de ``data/res_company_data.xml``. Se deja el archivo para que la
versión siga existiendo en la cadena de migraciones.
"""


def migrate(cr, version):
    return
