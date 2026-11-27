from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestDcasaBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')

    def test_company_is_configured_for_panama(self):
        self.assertEqual(self.company.country_id, self.env.ref('base.pa'))
        self.assertEqual(self.company.chart_template, 'pa')
        self.assertEqual(self.company.currency_id, self.env.ref('base.USD'))

    def test_sales_are_in_usd(self):
        """El plan contable de Panamá deja PAB; ventas y listas de precios deben quedar en USD."""
        usd = self.env.ref('base.USD')
        pricelists = self.env['product.pricelist'].search([('company_id', 'in', [self.company.id, False])])
        self.assertEqual(pricelists.currency_id, usd)
        order = self.env['sale.order'].create({'partner_id': self.env['res.partner'].create({'name': 'X'}).id})
        self.assertEqual(order.currency_id, usd)

    def test_company_es_tommalo(self):
        """Lo único decidido de la empresa (docs/TOMMALO.md): el nombre y el país. Teléfono y correo, PENDIENTE."""
        self.assertEqual(self.company.name, 'Tommalo')
        self.assertEqual(self.company.partner_id.name, 'Tommalo', 'la ficha de la empresa va con ella')
        self.assertEqual(self.company.country_id, self.env.ref('base.pa'))
        self.assertFalse(self.company.phone, 'el teléfono lo da Tommalo: nunca el de otra empresa')
        self.assertFalse(self.company.email, 'el correo lo da Tommalo: nunca el de otra empresa')

    def test_company_ruc_dv_y_direccion_vacios_hasta_que_el_dueno_los_de(self):
        """RUC, DV, dirección, ciudad, web y lema vacíos: nunca inventados ni los de otra empresa."""
        for campo in ('vat', 'l10n_pa_dv', 'street', 'street2', 'city', 'website', 'report_header'):
            with self.subTest(campo=campo):
                self.assertFalse(self.company[campo], campo)
        self.assertFalse(self.company.partner_id.dcasa_ruc_display)

    def test_company_logo_es_el_marcador_provisional(self):
        """El logo de la empresa (documentos, sitio y correos) es el marcador provisional (PENDIENTE: el logo de Tommalo):
        dcasa_base/static/img/logo.png."""
        import base64

        from odoo.tools.misc import file_open
        with file_open('dcasa_base/static/img/logo.png', 'rb') as archivo:
            self.assertEqual(base64.b64decode(self.company.logo), archivo.read())

    def test_company_ruc_with_dv(self):
        """Cuando el dueño ponga el RUC y el DV, la ficha los muestra juntos (mismo formato de siempre)."""
        self.company.write({'vat': '1557-1-2026', 'l10n_pa_dv': '45'})
        self.assertEqual(self.company.partner_id.dcasa_ruc_display, '1557-1-2026 DV45')

    def test_default_sale_tax_is_itbms_7(self):
        tax = self.company.account_sale_tax_id
        self.assertEqual(tax.amount, 7.0)
        self.assertEqual(tax.type_tax_use, 'sale')

    def test_attachments_stored_in_database(self):
        location = self.env['ir.config_parameter'].sudo().get_param('ir_attachment.location')
        self.assertEqual(location, 'db')

    def test_ruc_display_without_dv(self):
        partner = self.env['res.partner'].create({'name': 'Eric Gómez G.', 'vat': '2-723-510'})
        self.assertEqual(partner.dcasa_ruc_display, '2-723-510')

    def test_dv_must_be_numeric(self):
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({'name': 'Cliente', 'vat': '8-1-1', 'l10n_pa_dv': 'X'})

    def test_dv_is_commercial_field(self):
        company = self.env['res.partner'].create({
            'name': 'Hotel Cliente S.A.', 'is_company': True, 'vat': '1557-1-2026', 'l10n_pa_dv': '45',
        })
        contact = self.env['res.partner'].create({'name': 'Compras', 'parent_id': company.id})
        self.assertEqual(contact.l10n_pa_dv, '45')

    def test_numbers_use_panama_format(self):
        lang = self.env['res.lang']._lang_get('es_419')
        self.assertEqual((lang.decimal_point, lang.thousands_sep), ('.', ','))


@tagged('post_install', '-at_install')
class TestAccesoFacturasEnVentas(TransactionCase):
    """Las facturas cargadas del sistema anterior no vienen de un pedido: se ven desde Ventas por este acceso."""

    def test_ventas_tiene_el_acceso_a_las_facturas_de_clientes(self):
        menu = self.env.ref('dcasa_base.menu_dcasa_ventas_facturas')
        self.assertEqual(menu.parent_id, self.env.ref('sale.menu_sale_invoicing'))
        self.assertEqual(menu.action, self.env.ref('account.action_move_out_invoice_type'))
        self.assertEqual(menu.group_ids, self.env.ref('account.group_account_invoice'))

    def test_quien_factura_lo_ve_y_quien_no_tiene_permiso_no(self):
        menu = self.env.ref('dcasa_base.menu_dcasa_ventas_facturas')
        facturador = new_test_user(self.env, login='dc_facturador_menu', groups='account.group_account_invoice')
        solo_ventas = new_test_user(self.env, login='dc_solo_ventas_menu', groups='sales_team.group_sale_salesman')
        self.assertIn(menu.id, self.env['ir.ui.menu'].with_user(facturador)._visible_menu_ids())
        self.assertNotIn(menu.id, self.env['ir.ui.menu'].with_user(solo_ventas)._visible_menu_ids())
