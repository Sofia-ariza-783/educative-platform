import pytest
from fastapi.testclient import TestClient

from app.almacenamiento import AlmacenEnMemoria
from app.banco_items import BancoItems
from app.dominio import Area
from app.main import crear_app
from app.motor import MotorDiagnostico

CLAVE_PRUEBAS = b"clave-de-pruebas"
TIEMPO_ESTIMADO_S = 60.0
CORRECTA = "A"
INCORRECTA = "B"


def crudos_controlados(items_por_nivel: int = 10, niveles=range(1, 7)) -> list[dict]:
    """Ítems con respuesta conocida ("A") y 60 s estimados, para pruebas deterministas."""
    return [
        {
            "id": f"{area.value}-n{nivel}-{k:02d}",
            "area": area.value,
            "nivel": nivel,
            "enunciado": f"Ítem de prueba {area.value} nivel {nivel} número {k}",
            "opciones": ["uno", "dos", "tres", "cuatro"],
            "respuesta_correcta": CORRECTA,
            "tiempo_estimado_s": TIEMPO_ESTIMADO_S,
        }
        for area in Area
        for nivel in niveles
        for k in range(items_por_nivel)
    ]


@pytest.fixture
def banco() -> BancoItems:
    return BancoItems.desde_crudos(crudos_controlados(), CLAVE_PRUEBAS)


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def motor(banco, almacen) -> MotorDiagnostico:
    return MotorDiagnostico(banco, almacen)


@pytest.fixture
def cliente(motor) -> TestClient:
    return TestClient(crear_app(motor))


def contestar(motor: MotorDiagnostico, sesion_id: str, correcta: bool, tiempo_s: float = 30.0):
    """Responde el ítem que se está mostrando, acertando o fallando a propósito."""
    item = motor.item_actual(sesion_id)
    return motor.responder(sesion_id, item.id, CORRECTA if correcta else INCORRECTA, tiempo_s)
