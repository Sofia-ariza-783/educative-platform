# Prompt refinado (v2)

Este prompt reúne en un solo texto las iteraciones de la [Parte C](04-validacion-y-refinamiento.md). Las partes nuevas o precisadas respecto al v1 están marcadas con `[NUEVO]`.

```text
Quiero que generes el código de un componente llamado: C4 Motor de diagnóstico
Tipo: Servicio
Lenguaje/Framework preferido: Python 3.11+ con FastAPI y Pydantic v2, pruebas con pytest

Contexto: LeeCuenta es una app móvil de práctica adaptativa en lectura y
matemáticas para estudiantes de grados 6 a 9 de colegios oficiales (prioridad
rural). Funciona sin conexión.

Especificación del componente:
- Propósito: ubicar al estudiante en un nivel de 1 a 6 por área (lectura,
  matematicas), alineado a PISA y Saber.
- Entradas: estudiante_id, grado (6–9), área; por cada ítem: item_id,
  respuesta (letra A–D) y tiempo de respuesta en segundos. [NUEVO: formato]
- Salidas: resultado con id_evento (UUID), estudiante, grado, área, nivel final,
  porcentaje de respuestas apresuradas (1 decimal), total de ítems, motivo de
  cierre (nivel_estable | maximo_items | banco_agotado) y fecha. [NUEVO]
- Reglas de negocio:
  * Inicia en el nivel esperado del grado según una tabla configurable:
    6→2, 7→3, 8→4, 9→5. [NUEVO]
  * Dos aciertos seguidos suben un nivel y dos errores seguidos lo bajan.
    Tras cada cambio de nivel, ambas rachas vuelven a cero. [NUEVO]
  * El nivel nunca baja de 1 ni sube de 6. [NUEVO]
  * "Ítem estable" = respuesta que no cambia el nivel. Termina con 4 ítems
    estables seguidos o al llegar a 20 ítems. [NUEVO: definición]
  * Responder en menos del 30 % del tiempo estimado marca la respuesta como
    apresurada (exactamente el 30 % no lo es). [NUEVO: borde]
  * No repetir ítems en la sesión. Si el nivel se agota, usar el nivel más
    cercano (primero el inferior); si el área se agota, cerrar con
    banco_agotado. [NUEVO]
  * Es un diagnóstico: la API no revela si la respuesta fue correcta. [NUEVO]
- Flujo principal:
  1. POST /diagnosticos inicia la prueba y devuelve el primer ítem.
  2. GET /diagnosticos/{id}/item-actual muestra el ítem del nivel esperado.
  3. POST /diagnosticos/{id}/respuestas registra respuesta y tiempo.
  4. El motor ajusta el nivel y devuelve el siguiente ítem o el resultado.
  5. Al cerrar, guarda el resultado en C13 mediante una interfaz inyectable;
     GET /diagnosticos/{id}/resultado lo consulta. [NUEVO: contrato]
- RNF clave:
  * Siguiente ítem en < 300 ms con 2 GB de RAM: índice en memoria por
    (área, nivel); incluir un test de rendimiento con 6 000 ítems. [NUEVO]
  * Respuestas correctas protegidas: guardar solo HMAC-SHA256(clave, item_id +
    respuesta), clave por variable de entorno LEECUENTA_CLAVE_ITEMS, comparar
    con hmac.compare_digest. Ningún esquema de salida la incluye. [NUEVO]
  * Lector de pantalla: cada ítem incluye número de pregunta, opciones
    etiquetadas {clave, texto} y un campo etiqueta_accesible. [NUEVO]
  * Offline: la lógica de dominio no debe depender de FastAPI. [NUEVO]
- Criterios de aceptación (un test por criterio, nombrados ca1, ca2, ca3):
  * Dado un estudiante de grado 7, cuando inicia lectura, entonces el primer
    ítem es del nivel de grado 7.
  * Dados dos aciertos seguidos, cuando envía el segundo, entonces el siguiente
    ítem sube un nivel.
  * Dado un ítem de 60 s estimados, cuando responde a los 15 s, entonces queda
    marcado como apresurado.

Requerimientos adicionales para el código:
- Estructura modular: config (umbrales), dominio, motor (lógica pura),
  banco_items (C15), almacenamiento (Protocol hacia C13), modelos (Pydantic),
  rutas y main (fábrica crear_app con inyección del motor). [NUEVO]
- Validaciones con mensajes claros en español: grado 6–9, respuesta A–D,
  tiempo > 0, respuesta del ítem mostrado, sin respuestas tras el cierre.
  Errores: 404 sesión inexistente, 409 estado inválido, 422 con lista
  {campo, mensaje}. [NUEVO]
- Código comentado en español, con type hints y buenas prácticas de FastAPI.
- Pruebas: criterios de aceptación, reglas (bajar, topes, cierre por estabilidad
  y por 20, banco agotado, no repetir), seguridad y flujo HTTP con TestClient.
- README corto: ejecución, variables de entorno, endpoints, decisiones tomadas
  donde la spec no era explícita y limitaciones conocidas.
- Banco de ítems de ejemplo para ejecutar la demo, marcado como no pedagógico.
```

Anterior: [Validación y refinamiento](04-validacion-y-refinamiento.md) · Siguiente: [Validación con criterios](06-validacion-criterios.md)
