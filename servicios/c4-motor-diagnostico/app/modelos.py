"""Esquemas de entrada y salida de la API (Pydantic v2).

Los mensajes de validación están en español. `ItemPublico` nunca expone la
respuesta correcta ni su huella.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app import config
from app.dominio import Area, Item, MotivoCierre, ResultadoDiagnostico


class SolicitudInicio(BaseModel):
    estudiante_id: str = Field(description="Identificador del estudiante entregado por C2.")
    grado: int = Field(description="Grado escolar, de 6 a 9.")
    area: Area

    @field_validator("estudiante_id")
    @classmethod
    def validar_estudiante(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El identificador del estudiante es obligatorio.")
        return valor.strip()

    @field_validator("grado")
    @classmethod
    def validar_grado(cls, valor: int) -> int:
        if not config.GRADO_MIN <= valor <= config.GRADO_MAX:
            raise ValueError(f"El grado debe estar entre {config.GRADO_MIN} y {config.GRADO_MAX}.")
        return valor


class SolicitudRespuesta(BaseModel):
    item_id: str
    respuesta: str = Field(description="Letra de la opción elegida: A, B, C o D.")
    tiempo_respuesta_s: float = Field(description="Segundos desde que se mostró el ítem.")

    @field_validator("respuesta")
    @classmethod
    def validar_respuesta(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if valor not in config.CLAVES_OPCIONES:
            raise ValueError("La respuesta debe ser una de las opciones A, B, C o D.")
        return valor

    @field_validator("tiempo_respuesta_s")
    @classmethod
    def validar_tiempo(cls, valor: float) -> float:
        if valor <= 0:
            raise ValueError("El tiempo de respuesta debe ser mayor que cero.")
        return valor


class OpcionPublica(BaseModel):
    clave: str
    texto: str


class ItemPublico(BaseModel):
    """Ítem tal como lo muestra C3. Texto plano y opciones etiquetadas para lector de pantalla."""

    id: str
    area: Area
    nivel: int
    numero_pregunta: int
    max_preguntas: int
    enunciado: str
    opciones: list[OpcionPublica]
    tiempo_estimado_s: float
    etiqueta_accesible: str

    @classmethod
    def desde_item(cls, item: Item, numero_pregunta: int) -> "ItemPublico":
        opciones = [
            OpcionPublica(clave=clave, texto=texto)
            for clave, texto in zip(config.CLAVES_OPCIONES, item.opciones)
        ]
        lectura_opciones = ". ".join(f"Opción {o.clave}: {o.texto}" for o in opciones)
        return cls(
            id=item.id,
            area=item.area,
            nivel=item.nivel,
            numero_pregunta=numero_pregunta,
            max_preguntas=config.MAX_ITEMS,
            enunciado=item.enunciado,
            opciones=opciones,
            tiempo_estimado_s=item.tiempo_estimado_s,
            etiqueta_accesible=(
                f"Pregunta {numero_pregunta} de máximo {config.MAX_ITEMS}. "
                f"{item.enunciado} {lectura_opciones}."
            ),
        )


class ResultadoPublico(BaseModel):
    id_evento: str
    sesion_id: str
    estudiante_id: str
    grado: int
    area: Area
    nivel: int
    porcentaje_apresuradas: float
    total_items: int
    motivo_cierre: MotivoCierre
    finalizado_en: datetime

    @classmethod
    def desde_dominio(cls, resultado: ResultadoDiagnostico) -> "ResultadoPublico":
        return cls(**resultado.__dict__)


class RespuestaInicio(BaseModel):
    sesion_id: str
    area: Area
    nivel_inicial: int
    item: ItemPublico


class RespuestaRegistrada(BaseModel):
    """No informa si la respuesta fue correcta: el diagnóstico no da retroalimentación."""

    apresurada: bool
    finalizada: bool
    siguiente_item: ItemPublico | None = None
    resultado: ResultadoPublico | None = None
