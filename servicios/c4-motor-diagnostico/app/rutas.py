"""Endpoints HTTP del Motor de diagnóstico. Solo traducen entre la API y el motor."""

from fastapi import APIRouter, Depends, Request, status

from app.modelos import (
    ItemPublico,
    RespuestaInicio,
    RespuestaRegistrada,
    ResultadoPublico,
    SolicitudInicio,
    SolicitudRespuesta,
)
from app.motor import MotorDiagnostico

router = APIRouter(prefix="/diagnosticos", tags=["diagnóstico"])


def obtener_motor(request: Request) -> MotorDiagnostico:
    return request.app.state.motor


@router.post("", response_model=RespuestaInicio, status_code=status.HTTP_201_CREATED)
def iniciar_diagnostico(solicitud: SolicitudInicio, motor: MotorDiagnostico = Depends(obtener_motor)):
    sesion = motor.iniciar(solicitud.estudiante_id, solicitud.grado, solicitud.area)
    item = motor.item_actual(sesion.id)
    return RespuestaInicio(
        sesion_id=sesion.id,
        area=sesion.area,
        nivel_inicial=sesion.nivel_actual,
        item=ItemPublico.desde_item(item, numero_pregunta=1),
    )


@router.get("/{sesion_id}/item-actual", response_model=ItemPublico)
def item_actual(sesion_id: str, motor: MotorDiagnostico = Depends(obtener_motor)):
    item = motor.item_actual(sesion_id)
    numero = len(motor.obtener_sesion(sesion_id).respuestas) + 1
    return ItemPublico.desde_item(item, numero_pregunta=numero)


@router.post("/{sesion_id}/respuestas", response_model=RespuestaRegistrada)
def registrar_respuesta(
    sesion_id: str, solicitud: SolicitudRespuesta, motor: MotorDiagnostico = Depends(obtener_motor)
):
    resultado = motor.responder(
        sesion_id, solicitud.item_id, solicitud.respuesta, solicitud.tiempo_respuesta_s
    )
    if resultado.resultado is not None:
        return RespuestaRegistrada(
            apresurada=resultado.apresurada,
            finalizada=True,
            resultado=ResultadoPublico.desde_dominio(resultado.resultado),
        )
    numero = len(motor.obtener_sesion(sesion_id).respuestas) + 1
    return RespuestaRegistrada(
        apresurada=resultado.apresurada,
        finalizada=False,
        siguiente_item=ItemPublico.desde_item(resultado.siguiente_item, numero_pregunta=numero),
    )


@router.get("/{sesion_id}/resultado", response_model=ResultadoPublico)
def obtener_resultado(sesion_id: str, motor: MotorDiagnostico = Depends(obtener_motor)):
    return ResultadoPublico.desde_dominio(motor.resultado(sesion_id))
