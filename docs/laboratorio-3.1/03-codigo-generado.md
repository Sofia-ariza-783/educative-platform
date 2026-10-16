# Código generado

La versión final, ya refinada con el [prompt v2](05-prompt-refinado.md), está en
[`servicios/c4-motor-diagnostico/`](../../servicios/c4-motor-diagnostico/). Su
[README](../../servicios/c4-motor-diagnostico/README.md) explica cómo ejecutarla.

## Arquitectura

```
          HTTP (C3 Pantalla de diagnóstico)
                       │
      rutas.py ── modelos.py (Pydantic, mensajes en español)
                       │
                   motor.py          ← lógica pura, sin FastAPI
                  ╱         ╲
      banco_items.py      almacenamiento.py
      (C15, HMAC)         (puerto a C13)
                       │
                   config.py         ← umbrales y reglas numéricas
```

La lógica de negocio (`motor.py`) no importa FastAPI. Así puede ejecutarse dentro de la app móvil sin conexión, y la API HTTP queda como una capa delgada.

## Fragmentos principales

### Regla de respuesta apresurada (`app/motor.py`)

```python
def es_apresurada(tiempo_s: float, tiempo_estimado_s: float) -> bool:
    """Regla: menos del 30 % del tiempo estimado marca la respuesta como apresurada."""
    return tiempo_s < config.UMBRAL_APRESURADA * tiempo_estimado_s
```

### Ajuste de nivel por rachas (`app/motor.py`)

```python
@staticmethod
def _ajustar_nivel(sesion: SesionDiagnostico, correcta: bool) -> None:
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
```

### Regla de cierre (`app/motor.py`)

```python
@staticmethod
def _motivo_de_cierre(sesion: SesionDiagnostico) -> MotivoCierre | None:
    if sesion.items_estables >= config.ITEMS_ESTABLES_PARA_CERRAR:
        return MotivoCierre.NIVEL_ESTABLE
    if len(sesion.respuestas) >= config.MAX_ITEMS:
        return MotivoCierre.MAXIMO_ITEMS
    return None
```

### Respuestas correctas protegidas (`app/banco_items.py`)

```python
def calcular_huella(clave_secreta: bytes, item_id: str, respuesta: str) -> str:
    mensaje = f"{item_id}:{respuesta.strip().upper()}".encode()
    return hmac.new(clave_secreta, mensaje, hashlib.sha256).hexdigest()

def es_correcta(self, item: Item, respuesta: str) -> bool:
    huella = calcular_huella(self._clave, item.id, respuesta)
    return hmac.compare_digest(huella, item.huella_respuesta)
```

El banco solo guarda la huella HMAC de la respuesta correcta. Así, quien inspeccione los datos del celular no puede leer las respuestas, y `ItemPublico` nunca las expone en la API.

### Validación con mensajes en español (`app/modelos.py`)

```python
@field_validator("grado")
@classmethod
def validar_grado(cls, valor: int) -> int:
    if not config.GRADO_MIN <= valor <= config.GRADO_MAX:
        raise ValueError(f"El grado debe estar entre {config.GRADO_MIN} y {config.GRADO_MAX}.")
    return valor
```

### Ejemplo de uso real

```http
POST /diagnosticos
{"estudiante_id": "est-001", "grado": 7, "area": "matematicas"}
```

```json
{
  "sesion_id": "40a468d4-e607-4170-9136-5ea3fea1e6b7",
  "area": "matematicas",
  "nivel_inicial": 3,
  "item": {
    "id": "mat-n3-01", "nivel": 3, "numero_pregunta": 1, "max_preguntas": 20,
    "enunciado": "¿Cuánto es 9 × 5?",
    "opciones": [{"clave": "A", "texto": "45"}, {"clave": "B", "texto": "50"},
                 {"clave": "C", "texto": "36"}, {"clave": "D", "texto": "46"}],
    "tiempo_estimado_s": 60.0,
    "etiqueta_accesible": "Pregunta 1 de máximo 20. ¿Cuánto es 9 × 5? Opción A: 45. Opción B: 50. Opción C: 36. Opción D: 46."
  }
}
```

Anterior: [Prompt inicial](02-prompt-inicial.md) · Siguiente: [Validación y refinamiento](04-validacion-y-refinamiento.md)
