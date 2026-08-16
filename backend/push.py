"""Endpoints de suscripciones Web Push (PWA).

- `POST /api/push/subscribe`    registra la suscripción del dispositivo.
- `POST /api/push/unsubscribe`  la da de baja.
- `POST /api/push/test`         prueba de confirmación al propio dispositivo.
- `POST /api/push/broadcast`    aviso a todos (requiere `X-Admin-Token`).
"""

import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from lib.notificaciones import SubscriptionGoneError, enviar, notificar_todos
from lib.repository import PushSubscriptionRepository

router = APIRouter(prefix="/api/push", tags=["push"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


class SuscripcionEntrada(BaseModel):
    endpoint: str
    keys: dict[str, str] = Field(default_factory=dict)


class AvisoEntrada(BaseModel):
    titulo: str
    cuerpo: str = ""
    url: str = "/"


def _repo(db: Session) -> PushSubscriptionRepository:
    return PushSubscriptionRepository(db)


@router.post("/subscribe", status_code=201)
def suscribir(entrada: SuscripcionEntrada, db: Session = Depends(get_db)):
    """Registra (o actualiza) la suscripción del navegador."""
    if not entrada.endpoint:
        raise HTTPException(status_code=400, detail="endpoint requerido")
    sub = _repo(db).guardar(
        entrada.endpoint,
        (entrada.keys or {}).get("p256dh", ""),
        (entrada.keys or {}).get("auth", ""),
    )
    db.commit()
    return {"ok": True, "id": sub.id}


@router.post("/unsubscribe")
def desuscribir(entrada: SuscripcionEntrada, db: Session = Depends(get_db)):
    """Da de baja la suscripción (idempotente)."""
    _repo(db).eliminar(entrada.endpoint)
    db.commit()
    return {"ok": True}


@router.post("/test")
def prueba(entrada: SuscripcionEntrada, db: Session = Depends(get_db)):
    """Envía una notificación de prueba a la suscripción que la pide."""
    sub = _repo(db).por_endpoint(entrada.endpoint)
    if sub is None:
        raise HTTPException(status_code=404, detail="Suscripción no registrada")
    try:
        enviar(sub, "Frontera Grande", "¡Notificaciones activadas!", "/")
    except SubscriptionGoneError:
        _repo(db).eliminar(sub.endpoint)
        db.commit()
        raise HTTPException(status_code=410, detail="Suscripción ya no válida")
    db.commit()
    return {"ok": True}


@router.post("/broadcast")
def aviso_general(
    entrada: AvisoEntrada,
    db: Session = Depends(get_db),
    x_admin_token: str | None = Header(default=None),
):
    """Envía un aviso a todos los suscriptores (requiere token de admin)."""
    if not ADMIN_PASSWORD or x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Acción restringida al administrador")
    repo = _repo(db)
    enviadas = notificar_todos(repo, entrada.titulo, entrada.cuerpo, entrada.url)
    db.commit()
    return {"ok": True, "enviadas": enviadas}
