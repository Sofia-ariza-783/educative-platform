"""Puerto hacia el Almacenamiento local (C13).

El motor solo conoce el protocolo `AlmacenResultados`; la app móvil puede
inyectar la implementación real (base local cifrada) sin cambiar el motor.
"""

import json
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

from app.dominio import ResultadoDiagnostico


class AlmacenResultados(Protocol):
    def guardar(self, resultado: ResultadoDiagnostico) -> None: ...


class AlmacenEnMemoria:
    """Implementación para pruebas y desarrollo."""

    def __init__(self) -> None:
        self.resultados: list[ResultadoDiagnostico] = []

    def guardar(self, resultado: ResultadoDiagnostico) -> None:
        self.resultados.append(resultado)


class AlmacenArchivoJSONL:
    """Simula C13 con un archivo de una línea JSON por resultado.

    Cada línea es un evento con `id_evento` único listo para la cola de C14.
    """

    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta
        self._candado = threading.Lock()

    def guardar(self, resultado: ResultadoDiagnostico) -> None:
        registro = asdict(resultado)
        registro["area"] = resultado.area.value
        registro["motivo_cierre"] = resultado.motivo_cierre.value
        registro["finalizado_en"] = resultado.finalizado_en.isoformat()
        with self._candado:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            with self._ruta.open("a", encoding="utf-8") as archivo:
                archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
