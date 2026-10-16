"""Acceso al Banco de ítems y textos (C15).

Las respuestas correctas se protegen con HMAC-SHA256: el banco solo conserva una
huella de la clave correcta, de modo que un estudiante que inspeccione los datos
del celular no puede leer las respuestas. La comparación usa tiempo constante.
"""

import hashlib
import hmac
from collections.abc import Iterable, Mapping
from typing import Any

from app.config import CLAVES_OPCIONES, NIVEL_MAX, NIVEL_MIN
from app.dominio import Area, Item


def calcular_huella(clave_secreta: bytes, item_id: str, respuesta: str) -> str:
    """Huella de una respuesta: ligada al ítem para que no se pueda reutilizar entre ítems."""
    mensaje = f"{item_id}:{respuesta.strip().upper()}".encode()
    return hmac.new(clave_secreta, mensaje, hashlib.sha256).hexdigest()


class BancoItems:
    def __init__(self, items: Iterable[Item], clave_secreta: bytes):
        self._clave = clave_secreta
        self._por_id: dict[str, Item] = {}
        # Índice por (área, nivel) para elegir el siguiente ítem en O(ítems del nivel).
        self._por_area_nivel: dict[tuple[Area, int], list[Item]] = {}
        for item in items:
            self._por_id[item.id] = item
            self._por_area_nivel.setdefault((item.area, item.nivel), []).append(item)

    @classmethod
    def desde_crudos(cls, crudos: Iterable[Mapping[str, Any]], clave_secreta: bytes) -> "BancoItems":
        """Construye el banco a partir de ítems con `respuesta_correcta` en claro.

        La respuesta en claro se convierte en huella y se descarta de inmediato.
        """
        items = []
        for crudo in crudos:
            respuesta = str(crudo["respuesta_correcta"]).upper()
            if respuesta not in CLAVES_OPCIONES[: len(crudo["opciones"])]:
                raise ValueError(f"El ítem {crudo['id']} tiene una respuesta correcta inválida.")
            items.append(
                Item(
                    id=crudo["id"],
                    area=Area(crudo["area"]),
                    nivel=int(crudo["nivel"]),
                    enunciado=crudo["enunciado"],
                    opciones=tuple(crudo["opciones"]),
                    tiempo_estimado_s=float(crudo["tiempo_estimado_s"]),
                    huella_respuesta=calcular_huella(clave_secreta, crudo["id"], respuesta),
                )
            )
        return cls(items, clave_secreta)

    def obtener(self, item_id: str) -> Item | None:
        return self._por_id.get(item_id)

    def es_correcta(self, item: Item, respuesta: str) -> bool:
        huella = calcular_huella(self._clave, item.id, respuesta)
        return hmac.compare_digest(huella, item.huella_respuesta)

    def siguiente_item(self, area: Area, nivel: int, excluidos: set[str]) -> Item | None:
        """Primer ítem no usado del nivel pedido.

        Si el nivel se agotó, busca en el nivel más cercano (primero el inferior).
        Devuelve None cuando no queda ningún ítem del área.
        """
        for nivel_candidato in self._niveles_por_cercania(nivel):
            for item in self._por_area_nivel.get((area, nivel_candidato), []):
                if item.id not in excluidos:
                    return item
        return None

    @staticmethod
    def _niveles_por_cercania(nivel: int) -> list[int]:
        orden = [nivel]
        for distancia in range(1, NIVEL_MAX - NIVEL_MIN + 1):
            orden.extend([nivel - distancia, nivel + distancia])
        return [n for n in orden if NIVEL_MIN <= n <= NIVEL_MAX]


def crear_banco_ejemplo(clave_secreta: bytes, items_por_nivel: int = 6) -> BancoItems:
    """Banco de demostración para ejecutar el servicio sin el C15 real.

    Matemáticas usa operaciones generadas; lectura usa ítems de relleno marcados
    como ejemplo. No debe usarse con estudiantes.
    """
    crudos = []
    for nivel in range(NIVEL_MIN, NIVEL_MAX + 1):
        for k in range(items_por_nivel):
            a, b = 3 + nivel * 2 + k, 2 + nivel + k
            correcta = a * b
            # La opción correcta rota de posición para no quedar siempre en "A".
            posicion = k % len(CLAVES_OPCIONES)
            distractores = [str(correcta + b), str(correcta - a), str(correcta + 1)]
            opciones = distractores[:posicion] + [str(correcta)] + distractores[posicion:]
            crudos.append(
                {
                    "id": f"mat-n{nivel}-{k + 1:02d}",
                    "area": Area.MATEMATICAS.value,
                    "nivel": nivel,
                    "enunciado": f"¿Cuánto es {a} × {b}?",
                    "opciones": opciones,
                    "respuesta_correcta": CLAVES_OPCIONES[posicion],
                    "tiempo_estimado_s": 30 + nivel * 10,
                }
            )
            crudos.append(
                {
                    "id": f"lec-n{nivel}-{k + 1:02d}",
                    "area": Area.LECTURA.value,
                    "nivel": nivel,
                    "enunciado": f"[Ítem de ejemplo] Lee el texto de nivel {nivel} y elige la idea principal.",
                    "opciones": ["Idea principal", "Detalle secundario", "Opinión del autor", "Dato no mencionado"],
                    "respuesta_correcta": "A",
                    "tiempo_estimado_s": 45 + nivel * 15,
                }
            )
    return BancoItems.desde_crudos(crudos, clave_secreta)
