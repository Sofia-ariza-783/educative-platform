"""Criterios de aceptación de la especificación C4, uno por prueba."""

from app.config import NIVEL_ESPERADO_POR_GRADO
from app.dominio import Area
from tests.conftest import contestar


def test_ca1_grado_7_lectura_inicia_en_nivel_del_grado(cliente):
    """Dado un estudiante de grado 7, cuando inicia lectura, el primer ítem es del nivel de grado 7."""
    respuesta = cliente.post(
        "/diagnosticos", json={"estudiante_id": "est-001", "grado": 7, "area": "lectura"}
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nivel_inicial"] == NIVEL_ESPERADO_POR_GRADO[7]
    assert cuerpo["item"]["nivel"] == NIVEL_ESPERADO_POR_GRADO[7]
    assert cuerpo["item"]["area"] == "lectura"


def test_ca2_dos_aciertos_seguidos_suben_un_nivel(motor):
    """Dados dos aciertos seguidos, cuando envía el segundo, el siguiente ítem sube un nivel."""
    sesion = motor.iniciar("est-002", grado=7, area=Area.MATEMATICAS)
    nivel_inicial = sesion.nivel_actual

    contestar(motor, sesion.id, correcta=True)
    resultado = contestar(motor, sesion.id, correcta=True)

    assert resultado.siguiente_item.nivel == nivel_inicial + 1


def test_ca3_respuesta_a_15s_de_60s_estimados_es_apresurada(motor):
    """Dado un ítem de 60 s estimados, cuando responde a los 15 s, queda marcado como apresurado."""
    sesion = motor.iniciar("est-003", grado=8, area=Area.LECTURA)
    assert motor.item_actual(sesion.id).tiempo_estimado_s == 60

    resultado = contestar(motor, sesion.id, correcta=True, tiempo_s=15)

    assert resultado.apresurada is True
    assert sesion.respuestas[-1].apresurada is True
