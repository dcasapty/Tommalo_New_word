"""No hay pago contra entrega: «Pago al recibir o en tienda» pasa a llamarse «Pago en la tienda» con su mensaje nuevo
(models/tienda.py), y las copias por sitio de la portada se corrigen con ``TEXTOS_CORREGIDOS`` (vacío en Tommalo).
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['website']._dcasa_pagos()
    env['website']._dcasa_corregir_textos()
