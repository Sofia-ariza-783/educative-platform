"""Punto de entrada FastAPI del Motor de diagnóstico (C4)."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import config
from app.almacenamiento import AlmacenArchivoJSONL
from app.banco_items import crear_banco_ejemplo
from app.motor import (
    EntradaInvalida,
    ErrorDiagnostico,
    MotorDiagnostico,
    SesionEnCurso,
    SesionFinalizada,
    SesionNoEncontrada,
)
from app.rutas import router

logger = logging.getLogger(__name__)

_ESTADOS_POR_ERROR = {
    SesionNoEncontrada: status.HTTP_404_NOT_FOUND,
    SesionFinalizada: status.HTTP_409_CONFLICT,
    SesionEnCurso: status.HTTP_409_CONFLICT,
    EntradaInvalida: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _clave_items() -> bytes:
    clave = os.environ.get(config.VARIABLE_CLAVE_ITEMS)
    if not clave:
        logger.warning(
            "%s no está definida; se usa una clave de desarrollo.", config.VARIABLE_CLAVE_ITEMS
        )
        clave = "clave-solo-para-desarrollo"
    return clave.encode()


def _motor_por_defecto() -> MotorDiagnostico:
    ruta = Path(os.environ.get("LEECUENTA_RUTA_RESULTADOS", "datos/resultados.jsonl"))
    return MotorDiagnostico(crear_banco_ejemplo(_clave_items()), AlmacenArchivoJSONL(ruta))


def crear_app(motor: MotorDiagnostico | None = None) -> FastAPI:
    app = FastAPI(
        title="LeeCuenta · Motor de diagnóstico (C4)",
        description="Ubica al estudiante en un nivel de 1 a 6 por área (HU-01).",
        version="1.0.0",
    )
    app.state.motor = motor or _motor_por_defecto()
    app.include_router(router)

    @app.exception_handler(ErrorDiagnostico)
    async def manejar_error_negocio(_: Request, error: ErrorDiagnostico):
        codigo = _ESTADOS_POR_ERROR.get(type(error), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=codigo, content={"detalle": str(error)})

    @app.exception_handler(RequestValidationError)
    async def manejar_validacion(_: Request, error: RequestValidationError):
        errores = [
            {
                "campo": ".".join(str(parte) for parte in e["loc"][1:]),
                "mensaje": str(e["msg"]).removeprefix("Value error, "),
            }
            for e in error.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detalle": "Los datos enviados no son válidos.", "errores": errores},
        )

    return app


app = crear_app()
