"""Menú, entregas y pagos en bases que ya tenían el módulo (staging).

El menú se arma una sola vez al instalar (data/website_menu_data.xml, ``noupdate``) y las entregas y los pagos los
crea ``_dcasa_configurar_tienda`` al instalar: una actualización con ``-u`` no los vuelve a escribir. Aquí se corrige
una vez el menú y los nombres de las entregas (models/tienda.py).
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['website']._dcasa_sin_restos_de_dcasa()
