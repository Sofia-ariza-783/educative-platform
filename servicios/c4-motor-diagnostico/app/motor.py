"""Motor de diagnóstico (C4): ubica al estudiante en un nivel de 1 a 6 por área.

Lógica pura en Python, sin dependencias de FastAPI, para poder empaquetarla
dentro de la app móvil y ejecutarla sin conexión.

Flujo (spec C4):
  1. Inicia la prueba.             -> iniciar()
  2. Muestra un ítem del nivel.    -> item_actual()
  3. Registra respuesta y tiempo.  -> responder()
  4. Ajusta el nivel hasta cierre. -> _ajustar_nivel() / _motivo_de_cierre()
  5. Guarda el resultado en C13.   -> _cerrar()
"""

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from app import config
from app.almacenamiento import AlmacenResultados
from app.banco_items import BancoItems
from app.dominio import (
    Area,
    Item,
    MotivoCierre,
    RegistroRespuesta,
    ResultadoDiagnostico,
    SesionDiagnostico,
)


class ErrorDiagnostico(Exception):
    """Error de negocio con mensaje en español apto para mostrar al usuario."""


class SesionNoEncontrada(ErrorDiagnostico):
    pass


class SesionFinalizada(ErrorDiagnostico):
    pass


class SesionEnCurso(ErrorDiagnostico):
    pass


class EntradaInvalida(ErrorDiagnostico):
    pass


@dataclass(frozen=True)
class ResultadoRespuesta:
    apresurada: bool
    siguiente_item: Item | None
    resultado: ResultadoDiagnostico | None


def es_apresurada(tiempo_s: float, tiempo_estimado_s: float) -> bool:
    """Regla: menos del 30 % del tiempo estimado marca la respuesta como apresurada."""
    return tiempo_s < config.UMBRAL_APRESURADA * tiempo_estimado_s


def nivel_inicial(grado: int) -> int:
    """Regla: la prueba inicia en el nivel esperado para el grado."""
    if grado not in config.NIVEL_ESPERADO_POR_GRADO:
        raise EntradaInvalida(
            f"El grado debe estar entre {config.GRADO_MIN} y {config.GRADO_MAX}."
        )
    return config.NIVEL_ESPERADO_POR_GRADO[grado]


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class MotorDiagnostico:
    def __init__(
        self,
        banco: BancoItems,
        almacen: AlmacenResultados,
        reloj: Callable[[], datetime] = _ahora,
    ) -> None:
        self._banco = banco
        self._almacen = almacen
        self._reloj = reloj
        self._sesiones: dict[str, SesionDiagnostico] = {}
        self._candado = threading.Lock()

    # --- Paso 1: iniciar -------------------------------------------------

    def iniciar(self, estudiante_id: str, grado: int, area: Area) -> SesionDiagnostico:
        if not estudiante_id or not estudiante_id.strip():
            raise EntradaInvalida("El identificador del estudiante es obligatorio.")
        sesion = SesionDiagnostico(
            id=str(uuid.uuid4()),
            estudiante_id=estudiante_id.strip(),
            grado=grado,
            area=area,
            nivel_actual=nivel_inicial(grado),
            iniciada_en=self._reloj(),
        )
        with self._candado:
            self._presentar_siguiente(sesion)
            if sesion.item_actual_id is None:
                raise ErrorDiagnostico("No hay ítems disponibles para esta área.")
            self._sesiones[sesion.id] = sesion
        return sesion

    # --- Paso 2: mostrar ítem --------------------------------------------

    def obtener_sesion(self, sesion_id: str) -> SesionDiagnostico:
        sesion = self._sesiones.get(sesion_id)
        if sesion is None:
            raise SesionNoEncontrada("La sesión de diagnóstico no existe.")
        return sesion

    def item_actual(self, sesion_id: str) -> Item:
        sesion = self.obtener_sesion(sesion_id)
        if sesion.finalizada:
            raise SesionFinalizada("El diagnóstico ya terminó; consulta el resultado.")
        return self._banco.obtener(sesion.item_actual_id)

    # --- Pasos 3 y 4: registrar y ajustar --------------------------------

    def responder(
        self, sesion_id: str, item_id: str, respuesta: str, tiempo_s: float
    ) -> ResultadoRespuesta:
        with self._candado:
            sesion = self.obtener_sesion(sesion_id)
            if sesion.finalizada:
                raise SesionFinalizada("El diagnóstico ya terminó; no se reciben más respuestas.")
            if item_id != sesion.item_actual_id:
                raise EntradaInvalida("La respuesta no corresponde a la pregunta que se está mostrando.")
            if tiempo_s <= 0:
                raise EntradaInvalida("El tiempo de respuesta debe ser mayor que cero.")

            item = self._banco.obtener(item_id)
            clave = respuesta.strip().upper()
            if clave not in config.CLAVES_OPCIONES[: len(item.opciones)]:
                raise EntradaInvalida("La respuesta debe ser una de las opciones mostradas.")

            correcta = self._banco.es_correcta(item, clave)
            apresurada = es_apresurada(tiempo_s, item.tiempo_estimado_s)
            sesion.respuestas.append(
                RegistroRespuesta(
                    item_id=item.id,
                    nivel_item=item.nivel,
                    correcta=correcta,
                    tiempo_s=tiempo_s,
                    apresurada=apresurada,
                )
            )
            self._ajustar_nivel(sesion, correcta)

            motivo = self._motivo_de_cierre(sesion)
            if motivo is None:
                self._presentar_siguiente(sesion)
                if sesion.item_actual_id is None:
                    motivo = MotivoCierre.BANCO_AGOTADO
            if motivo is not None:
                self._cerrar(sesion, motivo)
                return ResultadoRespuesta(apresurada, None, sesion.resultado)

            return ResultadoRespuesta(apresurada, self._banco.obtener(sesion.item_actual_id), None)

    @staticmethod
    def _ajustar_nivel(sesion: SesionDiagnostico, correcta: bool) -> None:
        """Dos aciertos seguidos suben un nivel; dos errores seguidos lo bajan.

        Tras un cambio las rachas vuelven a cero, así tres aciertos seguidos
        suben un solo nivel. En los topes (1 y 6) la racha se consume sin cambio.
        """
        if correcta:
            sesion.racha_aciertos += 1
            sesion.racha_errores = 0
        else:
            sesion.racha_errores += 1
            sesion.racha_aciertos = 0

        nuevo_nivel = sesion.nivel_actual
        if sesion.racha_aciertos >= config.ACIERTOS_PARA_SUBIR:
            nuevo_nivel = min(config.NIVEL_MAX, sesion.nivel_actual + 1)
            sesion.racha_aciertos = 0
        elif sesion.racha_errores >= config.ERRORES_PARA_BAJAR:
            nuevo_nivel = max(config.NIVEL_MIN, sesion.nivel_actual - 1)
            sesion.racha_errores = 0

        if nuevo_nivel != sesion.nivel_actual:
            sesion.nivel_actual = nuevo_nivel
            sesion.items_estables = 0
        else:
            sesion.items_estables += 1

    @staticmethod
    def _motivo_de_cierre(sesion: SesionDiagnostico) -> MotivoCierre | None:
        """Termina con 4 ítems seguidos sin cambio de nivel o al llegar a 20 ítems."""
        if sesion.items_estables >= config.ITEMS_ESTABLES_PARA_CERRAR:
            return MotivoCierre.NIVEL_ESTABLE
        if len(sesion.respuestas) >= config.MAX_ITEMS:
            return MotivoCierre.MAXIMO_ITEMS
        return None

    def _presentar_siguiente(self, sesion: SesionDiagnostico) -> None:
        item = self._banco.siguiente_item(sesion.area, sesion.nivel_actual, sesion.items_usados)
        sesion.item_actual_id = item.id if item else None
        if item:
            sesion.items_usados.add(item.id)

    # --- Paso 5: cerrar y guardar en C13 ---------------------------------

    def _cerrar(self, sesion: SesionDiagnostico, motivo: MotivoCierre) -> None:
        total = len(sesion.respuestas)
        apresuradas = sum(1 for r in sesion.respuestas if r.apresurada)
        sesion.item_actual_id = None
        sesion.resultado = ResultadoDiagnostico(
            id_evento=str(uuid.uuid4()),
            sesion_id=sesion.id,
            estudiante_id=sesion.estudiante_id,
            grado=sesion.grado,
            area=sesion.area,
            nivel=sesion.nivel_actual,
            porcentaje_apresuradas=round(100 * apresuradas / total, 1) if total else 0.0,
            total_items=total,
            motivo_cierre=motivo,
            finalizado_en=self._reloj(),
        )
        self._almacen.guardar(sesion.resultado)

    def resultado(self, sesion_id: str) -> ResultadoDiagnostico:
        sesion = self.obtener_sesion(sesion_id)
        if not sesion.finalizada:
            raise SesionEnCurso("El diagnóstico todavía está en curso.")
        return sesion.resultado
