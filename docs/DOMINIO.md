# Dominio propio de Tommalo (PENDIENTE)

Tommalo todavía no tiene dominio en Cloudflare. Mientras tanto el sitio responde en su dirección `workers.dev`
(`https://tommalo.SUBDOMINIO-PENDIENTE.workers.dev`, cuando exista la cuenta) y `edge/wrangler.jsonc` lleva
`"routes": []`. El procedimiento completo y sus trampas están en [REPLICAR.md §6.8](REPLICAR.md) y
[DESPLIEGUE.md](DESPLIEGUE.md); resumen:

1. Agregar el dominio a Cloudflare copiando antes los registros DNS (sobre todo el correo) y esperar «Active».
2. Dar al token de despliegue *Zone › Workers Routes › Edit*.
3. En `edge/wrangler.jsonc`: `routes` con el dominio y `www`, `"workers_dev": true`, `"routes": []` en staging; ajustar las
   pruebas de `edge/test/` en el mismo cambio.
4. `URL_SITIO` de GitHub = `https://<dominio>`; `CANONICAL_HOST` vacía.
5. Registrar de nuevo el webhook de Brian, agregar el dominio a Access, Turnstile y Resend.

Nada de esto se hace hasta que el cliente tenga su dominio y dé el «sí».
