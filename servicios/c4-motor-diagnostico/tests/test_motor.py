"""Reglas de negocio y RNF del motor, probadas sin la capa HTTP."""

import time

import pytest

from app import config
from app.banco_items import BancoItems
from app.dominio import Area, MotivoCierre
from app.motor import (
    EntradaInvalida,
    MotorDiagnostico,
    SesionEnCurso,
    SesionFinalizada,
    es_apresurada,
)
from tests.conftest import CLAVE_PRUEBAS, CORRECTA, contestar, crudos_controlados


# --- Respuestas apresuradas ---------------------------------------------

@pytest.mark.parametrize(
    ("tiempo_s", "esperado"),
    [(15, True), (17.9, True), (18, False), (40, False)],
)
def test_umbral_de_respuesta_apresurada(tiempo_s, esperado):
    # 30 % de 60 s = 18 s; exactamente 18 s ya no es apresurada.
    assert es_apresurada(tiempo_s, 60) is esperado


def test_porcentaje_de_apresuradas_en_el_resultado(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.LECTURA)
    # Alternar acierto/error deja el nivel estable y cierra a los 4 ítems.
    contestar(motor, sesion.id, True, tiempo_s=10)   # apresurada
    contestar(motor, sesion.id, False, tiempo_s=40)
    contestar(motor, sesion.id, True, tiempo_s=40)
    contestar(motor, sesion.id, False, tiempo_s=40)

    assert motor.resultado(sesion.id).porcentaje_apresuradas == 25.0


# --- Ajuste de nivel ----------------------------------------------------

def test_dos_errores_seguidos_bajan_un_nivel(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.MATEMATICAS)
    contestar(motor, sesion.id, False)
    resultado = contestar(motor, sesion.id, False)
    assert resultado.siguiente_item.nivel == config.NIVEL_ESPERADO_POR_GRADO[7] - 1


def test_tres_aciertos_seguidos_suben_solo_un_nivel(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.MATEMATICAS)
    for _ in range(3):
        contestar(motor, sesion.id, True)
    assert sesion.nivel_actual == config.NIVEL_ESPERADO_POR_GRADO[7] + 1


def test_el_nivel_no_baja_de_1(motor):
    sesion = motor.iniciar("est", grado=6, area=Area.LECTURA)  # inicia en 2
    for _ in range(4):
        contestar(motor, sesion.id, False)
    assert sesion.nivel_actual == config.NIVEL_MIN


def test_el_nivel_no_sube_de_6(motor):
    sesion = motor.iniciar("est", grado=9, area=Area.LECTURA)  # inicia en 5
    for _ in range(4):
        if sesion.finalizada:
            break
        contestar(motor, sesion.id, True)
    assert sesion.nivel_actual == config.NIVEL_MAX


# --- Cierre de la prueba ------------------------------------------------

def test_cierra_con_4_items_estables_y_guarda_en_c13(motor, almacen):
    sesion = motor.iniciar("est-010", grado=7, area=Area.LECTURA)
    for correcta in (True, False, True, False):
        resultado = contestar(motor, sesion.id, correcta)

    assert resultado.resultado is not None
    final = motor.resultado(sesion.id)
    assert final.motivo_cierre is MotivoCierre.NIVEL_ESTABLE
    assert final.total_items == 4
    assert final.nivel == config.NIVEL_ESPERADO_POR_GRADO[7]
    assert almacen.resultados == [final]


def test_cierra_a_los_20_items_si_el_nivel_no_se_estabiliza(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.MATEMATICAS)
    # Sube y baja sin parar: nunca hay 4 ítems seguidos sin cambio.
    patron = [True, True, False, False] * 5
    for correcta in patron:
        contestar(motor, sesion.id, correcta)

    final = motor.resultado(sesion.id)
    assert final.motivo_cierre is MotivoCierre.MAXIMO_ITEMS
    assert final.total_items == config.MAX_ITEMS


def test_cierra_si_el_banco_se_agota():
    banco = BancoItems.desde_crudos(crudos_controlados(items_por_nivel=1, niveles=[3]), CLAVE_PRUEBAS)
    motor = MotorDiagnostico(banco, almacen=type("Nulo", (), {"guardar": lambda self, r: None})())
    sesion = motor.iniciar("est", grado=7, area=Area.LECTURA)
    contestar(motor, sesion.id, True)
    assert motor.resultado(sesion.id).motivo_cierre is MotivoCierre.BANCO_AGOTADO


def test_si_el_nivel_se_agota_usa_el_mas_cercano():
    banco = BancoItems.desde_crudos(crudos_controlados(items_por_nivel=1, niveles=[2, 3, 4]), CLAVE_PRUEBAS)
    motor = MotorDiagnostico(banco, almacen=type("Nulo", (), {"guardar": lambda self, r: None})())
    sesion = motor.iniciar("est", grado=7, area=Area.LECTURA)  # nivel 3, único ítem
    resultado = contestar(motor, sesion.id, True)
    assert resultado.siguiente_item.nivel == 2  # primero el inferior


def test_no_repite_items_en_la_misma_sesion(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.MATEMATICAS)
    vistos = []
    while not sesion.finalizada:
        vistos.append(motor.item_actual(sesion.id).id)
        contestar(motor, sesion.id, correcta=len(vistos) % 4 < 2)
    assert len(vistos) == len(set(vistos))


# --- Validaciones -------------------------------------------------------

@pytest.mark.parametrize("grado", [5, 10])
def test_rechaza_grados_fuera_de_rango(motor, grado):
    with pytest.raises(EntradaInvalida, match="El grado debe estar entre 6 y 9"):
        motor.iniciar("est", grado=grado, area=Area.LECTURA)


def test_rechaza_respuesta_a_un_item_que_no_se_esta_mostrando(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.LECTURA)
    with pytest.raises(EntradaInvalida, match="no corresponde"):
        motor.responder(sesion.id, "otro-item", CORRECTA, 30)


def test_rechaza_tiempo_no_positivo(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.LECTURA)
    item = motor.item_actual(sesion.id)
    with pytest.raises(EntradaInvalida, match="mayor que cero"):
        motor.responder(sesion.id, item.id, CORRECTA, 0)


def test_no_acepta_respuestas_despues_del_cierre(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.LECTURA)
    for correcta in (True, False, True, False):
        contestar(motor, sesion.id, correcta)
    with pytest.raises(SesionFinalizada):
        motor.responder(sesion.id, "cualquiera", CORRECTA, 30)


def test_resultado_no_disponible_durante_la_prueba(motor):
    sesion = motor.iniciar("est", grado=7, area=Area.LECTURA)
    with pytest.raises(SesionEnCurso):
        motor.resultado(sesion.id)


# --- RNF: seguridad y rendimiento ----------------------------------------

def test_el_banco_no_guarda_respuestas_en_texto_plano(banco):
    item = banco.obtener("lectura-n3-00")
    assert not hasattr(item, "respuesta_correcta")
    assert CORRECTA not in item.huella_respuesta
    assert banco.es_correcta(item, CORRECTA)
    assert not banco.es_correcta(item, "B")


def test_la_huella_cambia_con_la_clave():
    crudos = crudos_controlados(items_por_nivel=1, niveles=[1])
    banco_a = BancoItems.desde_crudos(crudos, b"clave-a")
    banco_b = BancoItems.desde_crudos(crudos, b"clave-b")
    item_a, item_b = banco_a.obtener("lectura-n1-00"), banco_b.obtener("lectura-n1-00")
    assert item_a.huella_respuesta != item_b.huella_respuesta


def test_siguiente_item_en_menos_de_300_ms_con_banco_grande():
    banco = BancoItems.desde_crudos(crudos_controlados(items_por_nivel=500), CLAVE_PRUEBAS)
    motor = MotorDiagnostico(banco, almacen=type("Nulo", (), {"guardar": lambda self, r: None})())
    sesion = motor.iniciar("est", grado=7, area=Area.MATEMATICAS)

    peor = 0.0
    for correcta in [True, True, False, False] * 5:
        inicio = time.perf_counter()
        contestar(motor, sesion.id, correcta)
        peor = max(peor, time.perf_counter() - inicio)

    assert peor < 0.300
