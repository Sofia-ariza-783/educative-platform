"""Entidades del dominio del diagnóstico, sin dependencias de FastAPI."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Area(str, Enum):
    LECTURA = "lectura"
    MATEMATICAS = "matematicas"


class MotivoCierre(str, Enum):
    NIVEL_ESTABLE = "nivel_estable"
    MAXIMO_ITEMS = "maximo_items"
    BANCO_AGOTADO = "banco_agotado"


@dataclass(frozen=True)
class Item:
    """Ítem del banco (C15). Nunca guarda la respuesta correcta en texto plano."""

    id: str
    area: Area
    nivel: int
    enunciado: str
    opciones: tuple[str, ...]
    tiempo_estimado_s: float
    huella_respuesta: str  # HMAC-SHA256 de la clave correcta


@dataclass(frozen=True)
class RegistroRespuesta:
    item_id: str
    nivel_item: int
    correcta: bool
    tiempo_s: float
    apresurada: bool


@dataclass(frozen=True)
class ResultadoDiagnostico:
    """Salida de C4 que se guarda en el almacenamiento local (C13)."""

    id_evento: str  # identificador único, lo usa C14 para descartar duplicados
    sesion_id: str
    estudiante_id: str
    grado: int
    area: Area
    nivel: int
    porcentaje_apresuradas: float
    total_items: int
    motivo_cierre: MotivoCierre
    finalizado_en: datetime


@dataclass
class SesionDiagnostico:
    id: str
    estudiante_id: str
    grado: int
    area: Area
    nivel_actual: int
    iniciada_en: datetime
    respuestas: list[RegistroRespuesta] = field(default_factory=list)
    items_usados: set[str] = field(default_factory=set)
    item_actual_id: str | None = None
    racha_aciertos: int = 0
    racha_errores: int = 0
    items_estables: int = 0  # respuestas seguidas sin cambio de nivel
    resultado: ResultadoDiagnostico | None = None

    @property
    def finalizada(self) -> bool:
        return self.resultado is not None
