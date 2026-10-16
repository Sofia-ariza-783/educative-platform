# Parte C · Validación y refinamiento

## 1. Revisión del código generado con el prompt v1

| Pregunta de revisión | Resultado v1 | Hallazgo |
|---|---|---|
| ¿Cumple con entradas/salidas? | Parcial | Recibía grado, área, respuesta y tiempo, y devolvía el nivel. El porcentaje de apresuradas y el motivo de cierre no estaban en un objeto de resultado claro. |
| ¿Aplica las reglas de negocio? | Parcial | "Inicia en el nivel del grado" se interpretó como nivel = grado (7 → nivel 7), que está fuera de la escala 1–6. "4 ítems estables" quedó sin definir. Las rachas no se reiniciaban tras subir, así que 3 aciertos podían contarse dos veces. |
| ¿Respeta los RNF? | No | La respuesta correcta se guardaba en texto plano y el endpoint del ítem la devolvía, así que el estudiante podía verla. No había ninguna medición de los 300 ms ni consideraciones de lector de pantalla. |
| ¿Incluye pruebas y documentación? | Parcial | Había pocas pruebas, no estaban ligadas a los criterios de aceptación y faltaban casos borde (topes 1 y 6, banco agotado). El README era genérico. |
| Calidad general | Parcial | La lógica estaba mezclada con los endpoints de FastAPI, lo que impide usarla sin conexión dentro de la app. Los mensajes de error eran los de Pydantic, en inglés. |

## 2. Iteraciones del prompt

Cada hallazgo se convirtió en una instrucción concreta. Estas son las iteraciones, en orden:

**Iteración 1: ambigüedad de reglas**
```text
El código interpreta "inicia en el nivel del grado" como nivel = grado, lo cual
sale de la escala 1–6. Usa esta tabla configurable: grado 6 → nivel 2,
7 → 3, 8 → 4, 9 → 5. Define "ítem estable" como una respuesta que no cambia el
nivel; la prueba termina con 4 seguidos. Tras cada cambio de nivel reinicia
ambas rachas, para que 3 aciertos seguidos suban un solo nivel. El nivel no
puede bajar de 1 ni subir de 6.
```

**Iteración 2: seguridad (RNF "respuestas correctas cifradas")**
```text
La respuesta correcta está en texto plano y el endpoint la devuelve. Guarda
solo una huella HMAC-SHA256 (clave por variable de entorno, ligada al id del
ítem) y compárala con hmac.compare_digest. Ningún esquema de salida puede
incluir la respuesta correcta. Como es un diagnóstico, la API tampoco debe decir
si la respuesta fue correcta.
```

**Iteración 3: validaciones y mensajes en español**
```text
Agrega validaciones con mensajes claros en español: grado entre 6 y 9,
respuesta A–D, tiempo mayor que cero, la respuesta debe corresponder al ítem
que se está mostrando, y no se aceptan respuestas tras el cierre.
Usa 404 si la sesión no existe, 409 por estado inválido y 422 con lista de
{campo, mensaje} para datos inválidos.
```

**Iteración 4: arquitectura offline y C13**
```text
Separa la lógica en un módulo de dominio sin dependencias de FastAPI para que
pueda empaquetarse en la app móvil. El guardado en C13 debe ser una interfaz
(Protocol) inyectable. Cada resultado lleva un id_evento UUID para que C14
descarte duplicados al sincronizar.
```

**Iteración 5: pruebas trazables y casos borde**
```text
Crea un archivo de pruebas con un test por cada criterio de aceptación,
nombrado ca1/ca2/ca3. Agrega pruebas de: dos errores bajan, topes 1 y 6,
cierre por estabilidad y por 20 ítems, banco agotado, no repetir ítems,
umbral exacto de apresurada (18 s de 60 s no es apresurada) y un test que
verifique < 300 ms por respuesta con un banco de 6 000 ítems.
```

**Iteración 6: accesibilidad del lado del servicio**
```text
Cada ítem debe incluir número de pregunta, opciones etiquetadas (clave + texto)
y un campo etiqueta_accesible con el texto completo que leerá el lector de
pantalla.
```

## 3. Resumen de mejoras entre v1 y v2

| Aspecto | v1 | v2 (final) |
|---|---|---|
| Nivel inicial | nivel = grado | Tabla configurable grado → nivel |
| Estabilidad / rachas | Indefinida / sin reinicio | Definida, con reinicio tras cada cambio |
| Respuestas correctas | Texto plano, expuestas | Huella HMAC, nunca expuestas |
| Validaciones | Defaults de Pydantic en inglés | Reglas de negocio + mensajes en español |
| Arquitectura | Lógica dentro de endpoints | Dominio puro + capa HTTP delgada |
| Integración C13/C14 | Implícita | Protocol inyectable + `id_evento` |
| Pruebas | Pocas y genéricas | 36 pruebas, 3 trazadas a criterios |
| Accesibilidad | No contemplada | `etiqueta_accesible` y opciones etiquetadas |

El prompt completo resultante está en [Prompt refinado (v2)](05-prompt-refinado.md).

Anterior: [Código generado](03-codigo-generado.md) · Siguiente: [Prompt refinado](05-prompt-refinado.md)
