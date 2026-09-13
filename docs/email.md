# Correo oficial `@fronteragrande.mx`

Configuración del correo con el dominio propio, gestionado por **Cloudflare**.
Decisión (2026-09-12): **solo recibir por ahora**; el envío queda pendiente
(mismo planteamiento que el roadmap #14: cuentas y correo oficial).

## Estado

- ✅ **Recibir:** `info@fronteragrande.mx` → `dhadaniel@gmail.com` (Email Routing), activo.
- ⏳ **Enviar:** pendiente, no configurado. Cuando se requiera, envío vía
  **Zoho Mail gratis** (SMTP) + "Enviar correo como" en Gmail.

## Cómo funciona

- `info@fronteragrande.mx` es una **dirección virtual** que no pertenece a Gmail:
  se registra contra el dominio en Cloudflare (Email Routing) y se **reenvía** al
  buzón real (`dhadaniel@gmail.com`). No hay buzón propio en Cloudflare.
- Para que *salga* correo firmado como `@fronteragrande.mx` se necesita un servidor
  **SMTP de ese dominio** (Cloudflare Email Routing no lo provee: solo reenvía).
  Opciones: Zoho Mail (gratis, hasta 1 usuario), Google Workspace (~$7 USD/mes),
  Microsoft 365 (~$6 USD/mes).

## Recibir (hecho)

1. Cloudflare → `fronteragrande.mx` → **Compute → Email Service → Email Routing**.
2. **Activate** → agrega al DNS automáticamente los registros de Email Routing:
   - 3 registros **MX**: `route1.mx.cloudflare.net` (prio 20), `route2` (85), `route3` (89).
   - **TXT SPF**: `v=spf1 include:_spf.mx.cloudflare.net ~all`.
   - **TXT DKIM**: `cf2024-1._domainkey.fronteragrande.mx` (clave pública, es pública a propósito).
3. **Destination addresses** → agregar `dhadaniel@gmail.com` → verificar con el
   correo de confirmación (estado *Verified*).
4. **Routing rules** → **Create routing rule**:
   - Email pattern: `info@fronteragrande.mx`
   - Action: **Send to an email** → `dhadaniel@gmail.com`
   - Estado: **Active**.
5. **Catch-all**: dejado en **Drop** (los correos a direcciones sin regla se
   descartan). Si algún día se quiere recibir todo, activarlo hacia el mismo Gmail.

Verificación de DNS (todos los MX deben apuntar a Cloudflare y estar propagados):

```bash
dig +short MX fronteragrande.mx
# 20 route1.mx.cloudflare.net.
# 85 route2.mx.cloudflare.net.
# 89 route3.mx.cloudflare.net.
```

> **Lección (2026-09-12):** justo tras activar Email Routing el primer correo de
> prueba rebota con `550 5.1.1 Address does not exist`. Es **propagación del DNS**:
> los registros tardan unos minutos en estar visibles globalmente. Reintentar la
> prueba minutos después; no es un error de configuración.

## Enviar (pendiente — pasos cuando se decida)

1. Crear cuenta gratis en [Zoho Mail](https://www.zoho.com/mail/) (plan **Free**,
   1 usuario, 1 dominio, 5 GB).
2. Verificar propiedad del dominio (TXT/DNS en Cloudflare) y crear `info@fronteragrande.mx`.
3. Gmail → Configuración → Cuentas e importación → **Enviar correo como** →
   agregar `info@fronteragrande.mx` con las credenciales **SMTP** de Zoho.
4. Resultado: se **recibe** en Gmail (Email Routing) y se **envía** como
   `@fronteragrande.mx` (SMTP de Zoho), sin costo.

## Cambiar el buzón destino

El destino no está atado a Gmail: en Cloudflare (Email Routing → Destination
addresses y Routing rules) se edita/agrega el correo receptor y la regla apunta
al nuevo. La dirección pública `info@fronteragrande.mx` no cambia.