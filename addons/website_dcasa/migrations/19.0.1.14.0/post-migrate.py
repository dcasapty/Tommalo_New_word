"""Corrige las copias por sitio de la portada con ``TEXTOS_CORREGIDOS`` (vacío en Tommalo); la descripción de la portada
la pone ``_dcasa_seo_portada`` en cada actualización.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['website']._dcasa_corregir_textos()
