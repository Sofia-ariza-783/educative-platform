# C4 · Motor de diagnóstico (LeeCuenta)

Servicio que ubica al estudiante en un **nivel de 1 a 6 por área** (lectura o matemáticas), alineado a PISA y Saber. Atiende la historia **HU-01** ("Presentar un diagnóstico para conocer mi nivel").

- **Tipo:** Servicio
- **Tecnología:** Python 3.11+ · FastAPI · Pydantic v2 · pytest
- **Depende de:** C15 Banco de ítems (lectura) y C13 Almacenamiento local (escritura)
- **Lo consume:** C3 Pantalla de diagnóstico

## Ejecución

```bash
cd servicios/c4-motor-diagnostico
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

# Clave para proteger las respuestas correctas del banco (obligatoria fuera de desarrollo)
set LEECUENTA_CLAVE_ITEMS=una-clave-larga-y-secreta     # Linux/macOS: export ...

uvicorn app.main:app --reload
```

La documentación interactiva queda en <http://127.0.0.1:8000/docs>.

Variables de entorno:

| Variable | Uso | Valor por defecto |
|---|---|---|
| `LEECUENTA_CLAVE_ITEMS` | Clave HMAC de las respuestas correctas | clave de desarrollo, con advertencia en el log |
| `LEECUENTA_RUTA_RESULTADOS` | Archivo JSONL que simula C13 | `datos/resultados.jsonl` |

## Pruebas

```bash
pytest -q
```

Las pruebas están en tres archivos:

- `tests/test_criterios_aceptacion.py`: un test por cada criterio de aceptación de la spec.
- `tests/test_motor.py`: reglas de negocio, validaciones, seguridad y rendimiento (< 300 ms).
- `tests/test_api.py`: flujo HTTP completo y contrato de la API.

## API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/diagnosticos` | Inicia la prueba. Cuerpo: `estudiante_id`, `grado` (6–9), `area` (`lectura` \| `matematicas`). Devuelve el primer ítem. |
| `GET` | `/diagnosticos/{sesion_id}/item-actual` | Ítem que se está mostrando. |
| `POST` | `/diagnosticos/{sesion_id}/respuestas` | Registra `item_id`, `respuesta` (A–D) y `tiempo_respuesta_s`. Devuelve el siguiente ítem o el resultado final. |
| `GET` | `/diagnosticos/{sesion_id}/resultado` | Nivel por área, porcentaje de respuestas apresuradas y motivo de cierre. |

Errores: `404` si la sesión no existe, `409` si la prueba ya terminó o aún no termina, `422` con mensajes en español si los datos no son válidos.

## Reglas implementadas

| Regla de la spec | Dónde |
|---|---|
| Inicia en el nivel del grado | `motor.nivel_inicial` + `config.NIVEL_ESPERADO_POR_GRADO` |
| Dos aciertos seguidos suben un nivel; dos errores lo bajan | `MotorDiagnostico._ajustar_nivel` |
| Termina a los 20 ítems o con 4 ítems estables | `MotorDiagnostico._motivo_de_cierre` |
| Menos del 30 % del tiempo estimado = apresurada | `motor.es_apresurada` |
| Guarda el resultado en C13 | `MotorDiagnostico._cerrar` → `AlmacenResultados.guardar` |

Decisiones tomadas donde la spec no era explícita:

- **Grado → nivel inicial:** 6→2, 7→3, 8→4, 9→5. Hay que validarlo con el equipo pedagógico; se cambia en `app/config.py`.
- **Ítem estable:** una respuesta que no cambia el nivel. Tras cada cambio de nivel las rachas vuelven a cero.
- **Topes:** el nivel no baja de 1 ni sube de 6. En los topes, la racha cuenta como ítem estable.
- **Nivel agotado:** si no quedan ítems del nivel se usa el más cercano, primero el inferior. Si el área se agota, la prueba cierra con `banco_agotado`.
- **Sin retroalimentación:** la API no dice si la respuesta fue correcta, porque es un diagnóstico y no una práctica.

## Estructura

```
app/
  config.py          Parámetros de negocio (umbrales, niveles, límites)
  dominio.py         Entidades puras: Item, SesionDiagnostico, ResultadoDiagnostico
  motor.py           Lógica del diagnóstico, sin FastAPI (se puede embeber en la app móvil)
  banco_items.py     Acceso a C15 y protección HMAC de las respuestas correctas
  almacenamiento.py  Puerto hacia C13 (memoria y archivo JSONL)
  modelos.py         Esquemas Pydantic de la API
  rutas.py           Endpoints
  main.py            Fábrica de la app y manejo de errores
tests/
```

## Limitaciones conocidas

- Las sesiones en curso viven en memoria del proceso. En el celular conviene persistirlas en C13 para resistir un cierre de la app.
- `crear_banco_ejemplo` genera ítems de demostración y **no** es contenido pedagógico real.
- El RNF de lector de pantalla se cumple del lado del servicio (texto plano, opciones etiquetadas y `etiqueta_accesible`). La verificación con TalkBack corresponde a C3.
