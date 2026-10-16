# LeeCuenta · educative-platform

> **Primera edición del proyecto.** El repositorio contiene el primer componente implementado (C4 Motor de diagnóstico) y la documentación del Laboratorio 3.1. Las validaciones pendientes quedan registradas para futuras verificaciones del equipo.

## Contexto

**LeeCuenta** es una app móvil de práctica adaptativa en **comprensión lectora** y **razonamiento matemático**. Funciona **sin conexión** en colegios oficiales. Responde a los resultados de PISA 2025: el **71 %** de los estudiantes no alcanza el nivel mínimo en matemáticas y el **54 %** no lo alcanza en lectura.

| Usuario | Rol |
|---|---|
| Estudiante de grados 6 a 9 (prioridad rural) | Usuario principal |
| Docente de lenguaje o matemáticas | Secundario: seguimiento y asignaciones |
| Acudiente | Secundario: resumen semanal |

### Historias de usuario del MVP

| ID | Rol | Historia |
|---|---|---|
| HU-01 | Estudiante | Presentar un diagnóstico para conocer mi nivel en lectura y matemáticas |
| HU-02 | Estudiante | Practicar a mi nivel con retroalimentación inmediata |
| HU-03 | Estudiante rural | Usar la app sin internet y sincronizar al tener señal |
| HU-04 | Docente | Ver niveles y alertas de rezago de mi curso |
| HU-05 | Docente | Asignar actividades a un grupo según su nivel |
| HU-06 | Acudiente | Recibir un resumen semanal del avance de mi hijo |

### Mapa de componentes (v1)

La app tiene 6 módulos y 17 componentes, de los cuales 15 forman el MVP. C7 y C17 quedan para una fase futura.

| Módulo | Componentes |
|---|---|
| M1 Acceso | C1 Ingreso por código de aula · C2 Autenticación y roles |
| M2 Diagnóstico | C3 Pantalla de diagnóstico · **C4 Motor de diagnóstico ✅** |
| M3 Práctica | C5 Pantalla de práctica · C6 Motor de adaptación · C7 Insignias (futuro) |
| M4 Docente | C8 Panel docente · C9 Analítica y alertas · C10 Asignador de actividades |
| M5 Familias | C11 Resumen semanal · C12 Mensajería WhatsApp/SMS |
| M6 Datos | C13 Almacenamiento local · C14 Sincronización diferida · C15 Banco de ítems · C16 Base de resultados · C17 SIMAT (futuro) |

Flujo de C4 dentro del sistema: **C3 → C4 → C15** (toma ítems del banco) y **C4 → C13 → C14 → C16** (el resultado se guarda en el celular y luego se sincroniza).

## Cómo moverse por el repositorio

```
educative-platform/
├── README.md                          ← estás aquí
├── docs/
│   └── laboratorio-3.1/               Implementación guiada por prompts
│       ├── README.md                  Índice y resumen del laboratorio
│       ├── 01-seleccion-componente.md Parte A: por qué C4 y su spec
│       ├── 02-prompt-inicial.md       Parte B: prompt v1 usado en Vibe Coding
│       ├── 03-codigo-generado.md      Arquitectura y fragmentos clave
│       ├── 04-validacion-y-refinamiento.md  Parte C: revisión e iteraciones
│       ├── 05-prompt-refinado.md      Prompt v2 con cambios marcados [NUEVO]
│       ├── 06-validacion-criterios.md Parte D: criterios y ajustes pendientes
│       └── 07-reflexion.md            Reflexión y autoevaluación
└── servicios/
    └── c4-motor-diagnostico/          C4 · Python + FastAPI
        ├── README.md                  Ejecución, API y reglas
        ├── requirements.txt / pyproject.toml
        ├── app/
        │   ├── config.py              Parámetros de negocio (umbrales, tablas)
        │   ├── dominio.py             Entidades: Item, Sesion, Resultado
        │   ├── motor.py               Lógica del diagnóstico (sin FastAPI)
        │   ├── banco_items.py         Acceso a C15 y protección HMAC
        │   ├── almacenamiento.py      Puerto hacia C13 (memoria / JSONL)
        │   ├── modelos.py             Esquemas Pydantic de la API
        │   ├── rutas.py               Endpoints
        │   └── main.py                Fábrica de la app y manejo de errores
        └── tests/
            ├── test_criterios_aceptacion.py  Un test por criterio (ca1–ca3)
            ├── test_motor.py                 Reglas, validaciones, RNF
            └── test_api.py                   Flujo HTTP completo
```

**Rutas de lectura sugeridas:**

- **Para evaluar el laboratorio:** `docs/laboratorio-3.1/README.md`, y luego los archivos 01 a 07 en orden.
- **Para entender el motor:** `app/config.py` (las reglas en números), luego `app/motor.py` (la lógica) y por último `tests/test_criterios_aceptacion.py`.
- **Para probar la API:** levanta el servicio y abre `/docs` (Swagger).

## Inicio rápido

Requisitos: Python 3.11 o superior.

```bash
cd servicios/c4-motor-diagnostico
python -m venv .venv
.venv\Scripts\activate              # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

pytest -q                           # 36 pruebas
uvicorn app.main:app --reload       # http://127.0.0.1:8000/docs
```

| Variable de entorno | Uso | Por defecto |
|---|---|---|
| `LEECUENTA_CLAVE_ITEMS` | Clave HMAC de las respuestas correctas | Clave de desarrollo, con advertencia en el log |
| `LEECUENTA_RUTA_RESULTADOS` | Archivo JSONL que simula C13 | `datos/resultados.jsonl` (ignorado por git) |

## C4 · Motor de diagnóstico

Ubica al estudiante en un **nivel de 1 a 6 por área** (lectura o matemáticas), alineado a PISA y Saber. Atiende la historia HU-01.

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/diagnosticos` | Inicia la prueba con `estudiante_id`, `grado` (6–9) y `area`. Devuelve el primer ítem |
| `GET` | `/diagnosticos/{id}/item-actual` | Devuelve el ítem que se está mostrando |
| `POST` | `/diagnosticos/{id}/respuestas` | Registra `item_id`, `respuesta` (A–D) y `tiempo_respuesta_s`. Devuelve el siguiente ítem o el resultado |
| `GET` | `/diagnosticos/{id}/resultado` | Devuelve nivel, porcentaje de apresuradas, total de ítems, motivo de cierre e `id_evento` |

Errores: `404` si la sesión no existe, `409` si el estado no es válido (prueba terminada o aún en curso) y `422` con una lista `{campo, mensaje}` en español.

**Reglas de la spec implementadas:**
- La prueba inicia en el nivel del grado.
- Dos aciertos seguidos suben un nivel y dos errores seguidos lo bajan.
- La prueba termina a los 20 ítems o con 4 ítems estables.
- Una respuesta en menos del 30 % del tiempo estimado es apresurada.
- El resultado se guarda en C13.

## Decisiones tomadas

| Decisión | Motivo |
|---|---|
| **Tabla grado → nivel inicial:** 6→2, 7→3, 8→4, 9→5 | La spec dice "inicia en el nivel del grado" pero no define la tabla. Esta es coherente con la alerta de C8 ("dos niveles por debajo de su grado"). Es configurable en `config.py` |
| **Ítem estable** = respuesta que no cambia el nivel | Hace operativa la regla "4 ítems estables" |
| **Las rachas se reinician tras cada cambio de nivel** | Así, tres aciertos seguidos suben un solo nivel |
| **Topes 1 y 6:** en el tope, la racha cuenta como ítem estable | Un estudiante en el máximo o el mínimo también estabiliza su resultado |
| **Exactamente el 30 % no es apresurada** | La regla dice "menos del 30 %" |
| **Si el nivel se agota, se usa el nivel más cercano** (primero el inferior). Si el área se agota, la prueba cierra con `banco_agotado` | Evita bloquear la prueba con bancos pequeños |
| **La API no revela si la respuesta fue correcta** | Es un diagnóstico, no una práctica, y así se protege el banco |
| **Las respuestas apresuradas sí cuentan para subir** | La spec de C4 no las excluye. C6 sí lo hace |
| **Lógica de dominio separada de FastAPI** | Para poder empaquetar el motor en la app móvil y usarlo sin conexión |
| **Respuestas correctas como huella HMAC-SHA256**, comparadas con `compare_digest` | Cumple el RNF "respuestas cifradas": no quedan en texto plano |
| **C13 se modela como un `Protocol` inyectable** | La app real puede conectar su base local sin tocar el motor |
| **Respuestas por letra (A–D)** en lugar de texto | Evita errores de comparación de texto y simplifica la accesibilidad |

## Puntos de interés

- **Umbrales centralizados.** Todos los valores numéricos de la spec (20 ítems, 4 estables, 30 %, rachas de 2) están en `app/config.py`. El equipo pedagógico puede ajustarlos sin tocar la lógica.
- **Trazabilidad.** Cada criterio de aceptación tiene su test (`test_ca1…`, `test_ca2…`, `test_ca3…`), así que cumplir un criterio es verificable de forma objetiva.
- **Listo para sincronizar.** Cada resultado lleva un `id_evento` (UUID) para que C14 descarte duplicados al reenviar lotes.
- **Accesibilidad desde el servicio.** Cada ítem trae `numero_pregunta`, opciones etiquetadas `{clave, texto}` y `etiqueta_accesible` con el texto completo para el lector de pantalla.
- **Rendimiento probado.** Un test verifica menos de 300 ms por respuesta con un banco de 6 000 ítems, gracias al índice en memoria por (área, nivel).
- **Banco de ejemplo.** `crear_banco_ejemplo` genera ítems de demostración (multiplicaciones y lecturas de relleno). **No es contenido pedagógico real.**
- **Proceso con IA documentado.** `docs/laboratorio-3.1` muestra el prompt v1, 6 iteraciones de refinamiento, el prompt v2 y los aprendizajes sobre cómo guiar a la IA.

## Estado y validaciones pendientes

**Estado actual:** los 3 criterios de aceptación de C4 se cumplen y las 36 pruebas automatizadas pasan.

## Próximos componentes

Por dependencias: **C6** (consume el nivel de C4), **C13/C14** (reciben sus resultados) y **C3** (su interfaz).

**Tecnología:** Python 3.11+ · FastAPI · Pydantic v2 · Uvicorn · pytest

## Repositorio

🔗 **https://github.com/Sofia-ariza-783/educative-platform**
