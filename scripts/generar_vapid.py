"""Genera un par de llaves VAPID para Web Push (PWA).

Imprime las variables listas para copiar a `.env` (y a los secrets de
Render/GitHub Actions):

    VAPID_PUBLIC_KEY=<clave pública para el navegador (base64url)>
    VAPID_PRIVATE_KEY=<clave privada para firmar (base64url)>
    VAPID_SUBJECT=mailto:info@fronteragrande.mx

Uso:
    .venv/bin/python scripts/generar_vapid.py
"""

import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid


def main() -> None:
    v = Vapid()
    v.generate_keys()

    priv = v.private_key.private_numbers().private_value
    priv_b64 = base64.urlsafe_b64encode(priv.to_bytes(32, "big")).rstrip(b"=").decode()

    pub = v.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64 = base64.urlsafe_b64encode(pub).rstrip(b"=").decode()

    print("VAPID_PUBLIC_KEY=" + pub_b64)
    print("VAPID_PRIVATE_KEY=" + priv_b64)
    print("VAPID_SUBJECT=mailto:info@fronteragrande.mx")


if __name__ == "__main__":
    main()