import functools
import hashlib
import json
import math
import os
from urllib.parse import urlsplit

from markupsafe import Markup

from odoo import api, fields, models
from odoo.addons.dcasa_base import whatsapp
from odoo.addons.dcasa_socios.models import reglas as reglas_socios
from odoo.exceptions import ValidationError
from odoo.fields import Domain
from odoo.http import request
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.tools.misc import file_open, file_path

LOGO_DE_FABRICA = 'dcasa_base/static/img/logo.png'


@functools.cache
def _sha1_logo_de_fabrica():
    with file_open(LOGO_DE_FABRICA, 'rb') as archivo:
        return hashlib.sha1(archivo.read()).hexdigest()


# El nombre con que el sitio saluda en los mensajes de WhatsApp ya escritos.
MARCA = 'Tommalo'

# Tommalo vende 100% en línea, sin tienda física: en lugar de una dirección y un mapa, el sitio dice esta frase. La usan
# «Contacto» (/visitanos), el pie y la portada. PENDIENTE (lo decide Tommalo): las zonas de entrega reales.
COBERTURA = 'Venta 100% online con entrega a domicilio en Panamá'

DEFAULT_WHATSAPP_MESSAGE = f'Hola {MARCA}, quiero información'

# Hosts que nunca deben salir en los datos estructurados: son de la máquina, no del sitio.
HOSTS_LOCALES = ('localhost', '0.0.0.0', '::1')

# Título y descripción de la portada para Google. PENDIENTE: Tommalo escribe los suyos (Sitio web > SEO); mientras
# tanto, frases neutras sin promesas.
SEO_PORTADA = {
    'website_meta_title': 'Tommalo Panamá | Tienda en línea',
    'website_meta_description': (
        'Tommalo: tienda en línea de belleza, hogar y salud con entrega a domicilio en Panamá.'),
}
# Valores que se pueden pisar: vacíos y los de ejemplo de Odoo. Lo que se escriba desde el editor (Sitio web > SEO) no
# se toca.
SEO_PORTADA_REEMPLAZABLES = {
    'website_meta_title': {''},
    'website_meta_description': {
        '',
        'This is the homepage of the website',
        'Esta es la página principal del sitio web',
        'Esta es la página de inicio del sitio web',
    },
}

# Las dos listas de abajo solo las usan migraciones viejas (19.0.1.8.0, 19.0.1.13.0, 19.0.1.14.0) de las bases de las
# tiendas de origen: en una instalación nueva no corren y no llevan textos de ningún negocio.
PROMESAS_RETIRADAS = []

# Textos de la portada que ya no son ciertos, para corregir en las copias por sitio (solo coincidencias exactas).
# Vacío en la base de Tommalo.
TEXTOS_CORREGIDOS = []

# Categorías de la tienda que ofrece la búsqueda sin resultados (xmlid sin prefijo, nombre): las cuatro del proveedor.
# Solo salen las que tienen algo publicado (``_dcasa_categorias``, models/buscador.py).
CATEGORIAS_PORTADA = [
    ('belleza', 'Belleza'),
    ('hogar', 'Hogar'),
    ('salud', 'Salud'),
    ('otro', 'Otros'),
]

# Menú principal: solo el catálogo. Tommalo escribe sus páginas (beneficios, historia, cómo comprar, preguntas) cuando
# decida su mensaje y las agrega desde Sitio web > Menú. Socios, Mi cuenta y Contacto siguen en el pie.
MENU_PRINCIPAL = [
    ('Productos', '/shop'),
]


def _es_menu_viejo(url):
    """Menús que el menú corto reemplaza: los de Odoo por defecto y los de una categoría."""
    url = url or ''
    return (url in ('/', '/shop', '/contactus', '/socios', '/#visitanos', '/visitanos')
            or url.startswith('/shop/category/'))


_RESENAS = {'mtime': None, 'datos': None}


def _leer_resenas():
    """data/resenas.json, leído una vez y releído solo si el archivo cambia."""
    ruta = file_path('website_dcasa/data/resenas.json')
    mtime = os.path.getmtime(ruta)
    if _RESENAS['mtime'] != mtime:
        with open(ruta, encoding='utf-8') as archivo:
            _RESENAS['datos'] = json.load(archivo)
        _RESENAS['mtime'] = mtime
    return _RESENAS['datos']


class Website(models.Model):
    _inherit = 'website'

    dcasa_whatsapp_number = fields.Char(
        string='WhatsApp de ventas',
        help='Número con código de país, p. ej. +507 6000-0002. Lo usan los botones de WhatsApp del sitio. '
             'Si está vacío se usa el teléfono de la empresa.',
    )

    # ------------------------------------------------------------------
    # WhatsApp
    # ------------------------------------------------------------------

    @api.constrains('dcasa_whatsapp_number')
    def _check_dcasa_whatsapp_number(self):
        """Un número inválido borraría en silencio todos los botones de WhatsApp del sitio."""
        for website in self.filtered('dcasa_whatsapp_number'):
            digitos = reglas_socios.solo_digitos(website.dcasa_whatsapp_number)
            if not (len(digitos) == 8 or 10 <= len(digitos) <= 15):
                raise ValidationError(self.env._(
                    'El WhatsApp de ventas debe ser un número, como +507 6000-0002 o 6000-0002.'))

    def _dcasa_whatsapp_numero(self):
        """El número de WhatsApp de ventas en dígitos, con el 507 de Panamá si son 8 (``'50760000001'``), o ``''``."""
        self.ensure_one()
        digits = reglas_socios.solo_digitos(self.dcasa_whatsapp_number or self.company_id.phone)
        if digits and len(digits) == 8:  # número de Panamá sin el código de país
            digits = f'507{digits}'
        return digits or ''

    def _dcasa_whatsapp_url(self, message=None):
        """El enlace de WhatsApp con el mensaje ya escrito (``api.whatsapp.com/send``, no ``wa.me``: en WhatsApp Web
        y en los navegadores de Instagram y Messenger ``wa.me`` cambia los emojis por «�»; dcasa_base/whatsapp.py),
        o ``'/contactus'`` si no hay número."""
        self.ensure_one()
        digits = self._dcasa_whatsapp_numero()
        if not digits:
            return '/contactus'
        return whatsapp.enlace(digits, message or DEFAULT_WHATSAPP_MESSAGE)

    def _dcasa_logo_de_fabrica(self):
        """¿El logo del sitio sigue siendo el de fábrica que trae el módulo (dcasa_base)?

        Entonces la cabecera usa su copia en WebP (3-7 KB, static/src/img/logo-*.webp) en lugar del
        PNG de 56 KB que pedía cada página con prioridad alta, compitiendo con la foto LCP. Si la
        dueña cambia el logo desde el editor, se muestra el suyo como siempre.
        """
        self.ensure_one()
        adjunto = self.env['ir.attachment'].sudo().search_read(
            [('res_model', '=', 'website'), ('res_field', '=', 'logo'), ('res_id', '=', self.id)],
            ['checksum'], limit=1)
        return bool(adjunto) and adjunto[0]['checksum'] == _sha1_logo_de_fabrica()

    def _dcasa_whatsapp_producto(self, product):
        """Mensaje de WhatsApp con el nombre del producto y su código público ya escritos (nunca la referencia del
        proveedor: la vendedora busca ese código en Productos y encuentra el producto)."""
        texto = f'Hola {MARCA}, me interesa: {product._dcasa_nombre_cliente()}'
        codigo = product.dcasa_codigo_publico
        return self._dcasa_whatsapp_url(f'{texto} (código {codigo})' if codigo else texto)

    def _dcasa_mas_itbms(self, producto):
        """¿Va «+ ITBMS» junto al precio? Sí, si la tienda muestra el precio sin impuesto y el
        producto lleva ITBMS: los precios del sitio son sin ITBMS y el 7 % se suma en el carrito."""
        self.ensure_one()
        return bool(
            self.show_line_subtotals_tax_selection == 'tax_excluded'
            # sudo: el visitante no lee impuestos; solo se pregunta si el producto lleva alguno.
            and producto.sudo().taxes_id._filter_taxes_by_company(self.company_id)
        )

    # ------------------------------------------------------------------
    # Menú
    # ------------------------------------------------------------------

    @api.model
    def _dcasa_armar_menu_principal(self):
        """Deja el menú de cada sitio en Catálogo · Socios Tommalo · Contacto.

        Solo quita los menús que reemplaza (Inicio, Tienda, Contáctanos, uno por categoría) y
        no duplica: se puede volver a correr sin perder lo que la dueña agregó desde el editor.
        """
        Menu = self.env['website.menu']
        idiomas = [codigo for codigo, _nombre in self.env['res.lang'].get_installed()]
        nuestros = {url for _nombre, url in MENU_PRINCIPAL}
        for website in self.search([]):
            raiz = website.menu_id
            if not raiz:
                continue
            raiz.child_id.filtered(lambda m: _es_menu_viejo(m.url) and m.url not in nuestros).unlink()
            for orden, (nombre, url) in enumerate(MENU_PRINCIPAL, start=1):
                valores = {'name': nombre, 'sequence': orden * 10}
                menu = raiz.child_id.filtered(lambda m, url=url: m.url == url)[:1]
                if menu:
                    menu.write(valores)  # p. ej. «Shop» de Odoo pasa a «Catálogo»
                else:
                    menu = Menu.create(dict(valores, url=url, parent_id=raiz.id, website_id=website.id))
                # El nombre es traducible: el mismo en todos los idiomas (si no, en español
                # seguiría la traducción de Odoo, «Tienda»).
                menu.update_field_translations('name', dict.fromkeys(idiomas, nombre))

    # ------------------------------------------------------------------
    # Portada
    # ------------------------------------------------------------------

    def _dcasa_categoria(self, clave):
        return self.env.ref(f'website_dcasa.public_category_{clave}', raise_if_not_found=False)

    def _dcasa_categoria_url(self, clave):
        """URL canónica (con slug) de una categoría de la tienda; '/shop' si ya no existe.

        En sudo: el visitante no puede leer una categoría aún sin productos, y el enlace igual sirve.
        """
        categoria = self._dcasa_categoria(clave)
        return f"/shop/category/{self.env['ir.http']._slug(categoria.sudo())}" if categoria else '/shop'

    def _dcasa_categoria_tiene_productos(self, clave):
        """¿Hay algo publicado y a la venta en esta categoría (o sus hijas) para este sitio?"""
        return bool(self._dcasa_categoria_cantidad(clave, limit=1))

    def _dcasa_categoria_cantidad(self, clave, limit=None):
        """Cuántos productos publicados y a la venta hay en esta categoría (o sus hijas) para este sitio: el número
        que la portada pone debajo de cada categoría (dato real del catálogo, nunca escrito a mano)."""
        categoria = self._dcasa_categoria(clave)
        if not categoria:
            return 0
        dominio = Domain.AND([self._dcasa_dominio_publicado(), [('public_categ_ids', 'child_of', categoria.sudo().id)]])
        return self.env['product.template'].sudo().search_count(dominio, limit=limit)

    def _dcasa_categorias(self):
        """Las categorías de la tienda con su URL real y cuántos productos publicados tienen.

        Una categoría sin nada publicado no lleva a una página vacía o de error: abre WhatsApp con el mensaje listo.
        Cuando se publique algo, vuelve sola a su página de la tienda (pedido de la dueña, 2026-11-09)."""
        self.ensure_one()
        tarjetas = []
        for clave, nombre in CATEGORIAS_PORTADA:
            cantidad = self._dcasa_categoria_cantidad(clave)
            con_productos = bool(cantidad)
            tarjetas.append({
                'clave': clave,
                'nombre': nombre,
                'cantidad': cantidad,
                'url': self._dcasa_categoria_url(clave) if con_productos else self._dcasa_whatsapp_url(
                    f'Hola {MARCA}, quiero información de {nombre.lower()}'),
                'whatsapp': not con_productos,
            })
        return tarjetas

    def _dcasa_dominio_publicado(self):
        """Lo que un visitante puede comprar: se vende en este sitio y está publicado.

        Lo usan los carruseles y el «Agregar» de un clic: los dos tienen que coincidir.
        """
        return Domain.AND([self.sale_product_domain(), [('is_published', '=', True)]])

    def _dcasa_productos(self, limit=8, categorias=None):
        """Productos publicados para los carruseles de la portada, con el mismo precio que la tienda.

        :param categorias: claves de categoría pública (p. ej. ``['belleza', 'hogar']``).
        """
        self.ensure_one()
        dominio = self._dcasa_dominio_publicado()
        if categorias:
            ids = [c.id for clave in categorias if (c := self._dcasa_categoria(clave))]
            dominio = Domain.AND([dominio, [('public_categ_ids', 'child_of', ids)]])
        productos = self.env['product.template'].search(dominio, limit=limit, order='website_sequence asc, id desc')
        # El precio y la moneda de la tarifa del visitante necesitan la petición web; sin ella, los de lista.
        con_tarifa = bool(productos) and bool(request) and hasattr(request, 'pricelist')
        precios = productos._get_sales_prices(self) if con_tarifa else {}
        moneda = (request.pricelist.currency_id if con_tarifa else None) or self.currency_id
        # Sin petición no hay visitante ni carrito: nada se compra en un clic.
        acceso = con_tarifa and self.has_ecommerce_access()
        items = []
        for p in productos:
            precio = precios.get(p.id, {}).get('price_reduce', p.list_price)
            items.append({
                'producto': p,
                'precio': precio,
                'moneda': moneda,
                'directo': acceso and self._dcasa_compra_directa(p, precio),
            })
        return items

    def _dcasa_hero_tarjeta(self):
        """El producto publicado más barato, como ``{'desde', 'moneda', 'url', 'nombre'}``, o ``False`` si no hay nada
        publicado (catálogo vacío: no sale nada). El precio se lee de Odoo como el de la tienda (nunca escrito a mano:
        CLAUDE.md, «un dato, un solo dueño»). La portada de la base no la dibuja (sin foto ni tarjeta fija); queda para
        cuando Tommalo decida su hero.
        """
        self.ensure_one()
        # En sudo: el visitante anónimo no lee algunos datos internos de la variante. Solo se expone lo publicado (el
        # precio y la ficha que ya ve cualquiera en la tienda).
        publicados = self.env['product.template'].sudo().search(self._dcasa_dominio_publicado())
        variantes = self.env['product.product'].sudo().search([('product_tmpl_id', 'in', publicados.ids)])
        if not variantes:
            return False
        con_tarifa = bool(request) and hasattr(request, 'pricelist')
        if con_tarifa:
            precios = [v._get_combination_info_variant()['price'] for v in variantes]
            moneda = request.pricelist.currency_id or self.currency_id
        else:
            precios = variantes.mapped('lst_price')
            moneda = self.currency_id
        barata = variantes[precios.index(min(precios))]
        plantilla = barata.product_tmpl_id
        return {'desde': min(precios), 'moneda': moneda, 'url': plantilla.website_url, 'nombre': plantilla.name}

    def _dcasa_compra_directa(self, producto, precio=None):
        """¿Se puede agregar al carrito sin pasar por la ficha?

        No, si hay que elegir algo (variantes, atributos configurables, combos, opcionales) o si
        la tienda no deja comprarlo así (precio cero bloqueado). Son las reglas del botón de Odoo.
        Los carruseles pasan el ``precio`` ya calculado para no volver a pasar por la tarifa
        producto por producto; sin precio, esa regla la revisa quien llama.
        """
        return bool(
            producto.product_variant_count == 1
            and not producto.has_configurable_attributes
            and producto.type != 'combo'
            and not producto.optional_product_ids
            and (precio is None or precio or not self.prevent_zero_price_sale)
        )

    def _dcasa_resenas(self):
        """Opiniones reales de la ficha de Google (copia literal en data/resenas.json).

        La cinta necesita repetir la lista para cerrar el bucle sin salto: ``copias`` dice
        cuántas veces se imprime (par, y cada mitad con al menos 8 tarjetas para cubrir
        pantallas anchas). Solo la primera copia la leen los lectores de pantalla.
        Un archivo incompleto no tumba la portada: la sección simplemente no sale.
        """
        try:
            datos = _leer_resenas()
        except (OSError, ValueError):
            return {'opiniones': []}
        opiniones = [
            o for o in datos.get('opiniones', [])
            if (o.get('texto') or '').strip() and o.get('autor') and o.get('estrellas')
        ]
        if not opiniones or not datos.get('ficha'):
            return {'opiniones': []}
        copias = 2 * math.ceil(8 / len(opiniones)) if len(opiniones) >= 3 else 1
        return {
            'ficha': datos['ficha'],
            'puntuacion': datos.get('puntuacion'),
            'total': datos.get('total'),
            'opiniones': opiniones,
            'copias': copias,
            'duracion': f'{max(30, round(len(opiniones) * copias * 5.5))}s',
        }

    def _dcasa_reglas_socios(self):
        """Cifras del programa de socios, leídas de puntos.json (nunca escritas a mano)."""
        return reglas_socios.cargar_reglas()

    def _dcasa_socios_con_cifras(self):
        """¿El programa de Socios ya tiene sus cifras (puntos por dólar, o los del referido)? Solo entonces la portada
        enseña su banda: con todo en PENDIENTE (Tommalo, 2026-11-18) prometería puntos que nadie gana. La portada de
        tommalo.example no la tiene; vuelve sola el día que el dueño ponga sus cifras en puntos.json."""
        reglas = self._dcasa_reglas_socios()
        referido = reglas.get('referido') or {}
        return bool((reglas.get('acumulacion') or {}).get('puntosPorDolar')
                    or (referido.get('puntosAlPadrino') and referido.get('puntosAlAhijado')))

    # ------------------------------------------------------------------
    # SEO
    # ------------------------------------------------------------------

    def _dcasa_url_publica(self):
        """URL pública del sitio para los datos estructurados; '' si solo hay una local.

        Sale de ``website.domain`` o, si está vacío, del parámetro ``web.base.url``
        (``get_base_url``). En el despliegue hay que fijar ``web.base.url`` con el dominio
        real (https://…) y ``web.base.url.freeze = True``: sin el «freeze», Odoo lo reescribe
        con la URL desde la que entra el administrador. Si aun así quedara una URL local
        (localhost, 127.x…), los JSON-LD salen sin URLs absolutas antes que mandarle a Google
        una dirección de la máquina.
        """
        self.ensure_one()
        base = (self.get_base_url() or '').rstrip('/')
        host = (urlsplit(base).hostname or '').lower()
        if not host or host in HOSTS_LOCALES or host.startswith('127.') or host.endswith('.localhost'):
            return ''
        return base

    def _dcasa_json_ld_organizacion(self, company=None):
        """JSON-LD ``Organization`` de todas las páginas (reemplaza el de website_sale).

        El de Odoo arma el JSON a mano con ``t-out``, que escapa para HTML: un nombre con apóstrofo salía como
        ``D&#39;Nombre`` dentro del JSON y Google lee el texto literal. Aquí va como JSON seguro
        para <script> (json_scriptsafe), y la URL nunca es la de una máquina local.
        """
        self.ensure_one()
        company = company or self.company_id
        base = self._dcasa_url_publica()
        datos = {
            '@context': 'https://schema.org',
            '@type': 'Organization',
            'name': company.name,
        }
        if base:
            datos['url'] = base
            datos['logo'] = self._dcasa_logo_publico(base)
        return json_scriptsafe.dumps(datos, ensure_ascii=False)

    def _dcasa_logo_publico(self, base):
        """El logo para Google, uno solo en todos los datos estructurados: el del sitio (el de la cabecera), en una
        dirección estable. Antes la portada decía dos distintos (``/logo.png?company=1`` y
        ``/web/image/website/1/logo?unique=…``, que cambiaba con cada cambio del sitio)."""
        self.ensure_one()
        return f'{base}/web/image/website/{self.id}/logo' if base else ''

    def _dcasa_json_ld(self):
        """Datos estructurados OnlineStore para Google: Tommalo vende en línea, sin tienda física (decisión del
        dueño, 2026-11-18). Sin coordenadas ni mapa: no hay local que ubicar. La dirección, solo con lo que la empresa
        tenga escrito (hoy, el país).

        JSON seguro dentro de <script> (escapa <, >, & y U+2028/9) con el helper de Odoo. El logo es el mismo que el de
        ``Organization`` (``_dcasa_logo_publico``).
        """
        self.ensure_one()
        company = self.company_id
        base = self._dcasa_url_publica()  # '' si solo hay una URL local: sin URLs absolutas
        datos = {
            '@context': 'https://schema.org',
            '@type': 'OnlineStore',
            '@id': base and f'{base}/#tienda',
            'name': company.name,
            'url': base,
            'logo': self._dcasa_logo_publico(base),
            'telephone': company.phone,
            'email': company.email,
            'currenciesAccepted': company.currency_id.name,
            'address': {
                '@type': 'PostalAddress',
                'streetAddress': ', '.join(filter(None, [company.street, company.street2])),
                'addressLocality': company.city,
                'addressRegion': company.state_id.name,
                'addressCountry': company.country_id.code or 'PA',
            },
            'sameAs': [url for url in (self.social_instagram, self.social_tiktok, self.social_facebook) if url],
        }
        # Sin campos vacíos (Google los marca como error). Nada de cifras inventadas (rango de precios).
        datos = {k: v for k, v in datos.items() if v}
        datos['address'] = {k: v for k, v in datos['address'].items() if v}
        return json_scriptsafe.dumps(datos, ensure_ascii=False)

    @api.model
    def _dcasa_seo_portada(self):
        """Título y descripción de la portada en todos los idiomas y en todas sus copias.

        Odoo crea una copia de la portada por sitio (``_bootstrap_homepage``) con su descripción
        de ejemplo, y la carga de traducciones pone la suya en español: un registro de datos sobre
        ``website.homepage_page`` no llegaba a lo que ve Google. Se corre en cada actualización y
        solo pisa valores vacíos o de ejemplo de Odoo.
        """
        idiomas = list(dict.fromkeys(['en_US', *(c for c, _n in self.env['res.lang'].get_installed())]))
        paginas = self.env['website.page'].sudo().with_context(active_test=False).search([('url', '=', '/')])
        for pagina in paginas:
            for idioma in idiomas:
                en_idioma = pagina.with_context(lang=idioma)
                valores = {
                    campo: valor for campo, valor in SEO_PORTADA.items()
                    if (en_idioma[campo] or '').strip() in SEO_PORTADA_REEMPLAZABLES[campo]
                    and en_idioma[campo] != valor
                }
                if valores:
                    en_idioma.write(valores)

    @api.model
    def _dcasa_retirar_promesas(self):
        """Quita las promesas sin respaldo (SW-03) de lo que quedó copiado fuera de las plantillas.

        Vistas por sitio (copias y bloques guardados desde el editor) y el mensaje del pago al
        recibir. Las plantillas del módulo ya traen el texto nuevo. Devuelve cuántos registros
        cambió.
        """
        idiomas = list(dict.fromkeys(['en_US', *(c for c, _n in self.env['res.lang'].get_installed())]))
        # Todas las promesas viejas de las vistas dicen «financiamiento»; se busca en todos los
        # idiomas a la vez (el texto traducido vive en el jsonb de arch_db).
        self.env['ir.ui.view'].flush_model(['arch_db', 'website_id', 'type'])
        self.env.cr.execute("""
            SELECT id FROM ir_ui_view
             WHERE website_id IS NOT NULL AND type = 'qweb' AND arch_db::text ILIKE '%%financiamiento%%'
        """)
        View = self.env['ir.ui.view'].sudo().with_context(active_test=False, no_cow=True)
        registros = [(vista, 'arch_db') for vista in View.browse(r[0] for r in self.env.cr.fetchall())]
        cod = self.env.ref('delivery.payment_provider_cod', raise_if_not_found=False)
        if cod:
            registros.append((cod.sudo(), 'pending_msg'))
        cambiados = 0
        for registro, campo in registros:
            tocado = False
            for idioma in idiomas:
                texto = registro.with_context(lang=idioma)[campo] or ''
                nuevo = str(texto)
                for viejo, reemplazo in PROMESAS_RETIRADAS:
                    nuevo = nuevo.replace(viejo, reemplazo)
                if nuevo != str(texto):
                    registro.with_context(lang=idioma).write(
                        {campo: Markup(nuevo) if isinstance(texto, Markup) else nuevo})
                    tocado = True
            cambiados += tocado
        return cambiados

    @api.model
    def _dcasa_corregir_textos(self):
        """Corrige TEXTOS_CORREGIDOS en las copias por sitio de la portada (todas las lenguas). Devuelve cuántas
        vistas cambió; se puede volver a correr."""
        idiomas = list(dict.fromkeys(['en_US', *(c for c, _n in self.env['res.lang'].get_installed())]))
        self.env['ir.ui.view'].flush_model(['arch_db', 'website_id', 'type'])
        condiciones = ' OR '.join(['arch_db::text ILIKE %s'] * len(TEXTOS_CORREGIDOS))
        self.env.cr.execute(
            f"SELECT id FROM ir_ui_view WHERE website_id IS NOT NULL AND type = 'qweb' AND ({condiciones})",
            [f'%{viejo[:60]}%' for viejo, _nuevo in TEXTOS_CORREGIDOS])
        View = self.env['ir.ui.view'].sudo().with_context(active_test=False, no_cow=True)
        cambiadas = 0
        for vista in View.browse(r[0] for r in self.env.cr.fetchall()):
            tocada = False
            for idioma in idiomas:
                texto = vista.with_context(lang=idioma).arch_db or ''
                nuevo = texto
                for viejo, reemplazo in TEXTOS_CORREGIDOS:
                    nuevo = nuevo.replace(viejo, reemplazo)
                if nuevo != texto:
                    vista.with_context(lang=idioma).write({'arch_db': nuevo})
                    tocada = True
            cambiadas += tocada
        return cambiadas
