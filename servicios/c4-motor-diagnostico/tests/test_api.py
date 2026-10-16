"""Flujo completo por HTTP y contrato de la API."""

from tests.conftest import CORRECTA, INCORRECTA


def _iniciar(cliente, grado=7, area="lectura"):
    respuesta = cliente.post(
        "/diagnosticos", json={"estudiante_id": "est-100", "grado": grado, "area": area}
    )
    assert respuesta.status_code == 201
    return respuesta.json()


def _responder(cliente, sesion_id, item_id, respuesta, tiempo=30):
    return cliente.post(
        f"/diagnosticos/{sesion_id}/respuestas",
        json={"item_id": item_id, "respuesta": respuesta, "tiempo_respuesta_s": tiempo},
    )


def test_flujo_completo_hasta_el_resultado(cliente):
    inicio = _iniciar(cliente)
    sesion_id, item = inicio["sesion_id"], inicio["item"]

    for respuesta in (CORRECTA, INCORRECTA, CORRECTA, INCORRECTA):
        cuerpo = _responder(cliente, sesion_id, item["id"], respuesta).json()
        item = cuerpo["siguiente_item"]

    assert cuerpo["finalizada"] is True
    resultado = cliente.get(f"/diagnosticos/{sesion_id}/resultado").json()
    assert resultado["area"] == "lectura"
    assert resultado["nivel"] == inicio["nivel_inicial"]
    assert resultado["porcentaje_apresuradas"] == 0.0
    assert resultado["motivo_cierre"] == "nivel_estable"
    assert resultado["id_evento"]


def test_el_item_publico_no_expone_la_respuesta(cliente):
    item = _iniciar(cliente)["item"]
    assert "huella_respuesta" not in item
    assert "respuesta_correcta" not in item
    assert [o["clave"] for o in item["opciones"]] == ["A", "B", "C", "D"]


def test_el_item_incluye_etiqueta_para_lector_de_pantalla(cliente):
    item = _iniciar(cliente)["item"]
    assert item["etiqueta_accesible"].startswith("Pregunta 1 de máximo 20.")
    assert "Opción A:" in item["etiqueta_accesible"]


def test_registrar_respuesta_no_revela_si_fue_correcta(cliente):
    inicio = _iniciar(cliente)
    cuerpo = _responder(cliente, inicio["sesion_id"], inicio["item"]["id"], CORRECTA).json()
    assert "correcta" not in cuerpo
    assert cuerpo["siguiente_item"]["numero_pregunta"] == 2


def test_grado_invalido_responde_422_en_espanol(cliente):
    respuesta = cliente.post(
        "/diagnosticos", json={"estudiante_id": "est", "grado": 5, "area": "lectura"}
    )
    assert respuesta.status_code == 422
    errores = respuesta.json()["errores"]
    assert errores == [{"campo": "grado", "mensaje": "El grado debe estar entre 6 y 9."}]


def test_respuesta_fuera_de_opciones_responde_422(cliente):
    inicio = _iniciar(cliente)
    respuesta = _responder(cliente, inicio["sesion_id"], inicio["item"]["id"], "E")
    assert respuesta.status_code == 422
    assert respuesta.json()["errores"][0]["mensaje"] == "La respuesta debe ser una de las opciones A, B, C o D."


def test_tiempo_cero_responde_422(cliente):
    inicio = _iniciar(cliente)
    respuesta = _responder(cliente, inicio["sesion_id"], inicio["item"]["id"], CORRECTA, tiempo=0)
    assert respuesta.status_code == 422


def test_sesion_inexistente_responde_404(cliente):
    respuesta = cliente.get("/diagnosticos/no-existe/item-actual")
    assert respuesta.status_code == 404
    assert respuesta.json() == {"detalle": "La sesión de diagnóstico no existe."}


def test_resultado_antes_de_terminar_responde_409(cliente):
    inicio = _iniciar(cliente)
    respuesta = cliente.get(f"/diagnosticos/{inicio['sesion_id']}/resultado")
    assert respuesta.status_code == 409


def test_item_actual_coincide_con_el_mostrado(cliente):
    inicio = _iniciar(cliente)
    actual = cliente.get(f"/diagnosticos/{inicio['sesion_id']}/item-actual").json()
    assert actual["id"] == inicio["item"]["id"]
