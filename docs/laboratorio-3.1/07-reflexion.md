# Reflexión final

## ¿Qué funcionó bien en el prompt?

- **Partir de una especificación estructurada.** Como el Laboratorio 2 ya tenía entradas, salidas, reglas, flujo, RNF y criterios separados, el prompt inicial salió completo y sin inventar nada. La IA generó desde el primer intento un servicio con la forma correcta: endpoints de inicio, respuesta y resultado.
- **Los criterios en formato Dado/Cuando/Entonces** se tradujeron casi directamente en pruebas. Fueron la parte del prompt que mejor guió a la IA.
- **Pedir el framework explícitamente** (FastAPI) evitó discusiones de tecnología y dio una estructura reconocible: routers, esquemas Pydantic y TestClient.

## ¿Qué tuve que mejorar?

- **Las ambigüedades de la spec.** "Inicia en el nivel del grado" y "4 ítems estables" eran claras para mí, pero no para la IA. Tuve que convertirlas en reglas operativas: una tabla grado → nivel, una definición de ítem estable y el reinicio de rachas. La IA resolvió las ambigüedades a su manera, y no siempre bien.
- **Los RNF de seguridad.** "Respuestas correctas cifradas" no bastó. La primera versión incluso devolvía la respuesta correcta en la API. Tuve que especificar el mecanismo (HMAC con clave por variable de entorno) y la prohibición explícita de exponerla.
- **Los casos borde.** Topes 1 y 6, banco agotado, umbral exacto del 30 %, respuestas fuera de orden: nada de esto aparece si no se pide.
- **La arquitectura.** Para que el componente funcione sin conexión, la lógica tenía que estar desacoplada de FastAPI. La IA no lo infirió del contexto "funciona sin conexión"; hubo que pedirlo.
- **El idioma de los mensajes** de error, que por defecto salían en inglés.

## ¿Qué aprendí sobre cómo guiar a la IA para programar?

1. **La IA completa los vacíos con supuestos, y a veces son incorrectos.** Cada ambigüedad de la spec se vuelve una decisión silenciosa en el código. Es mejor detectarlas antes y escribirlas como reglas verificables.
2. **Los RNF hay que traducirlos a técnica.** "Seguro", "rápido" o "accesible" no generan código. "HMAC-SHA256 + compare_digest", "índice por (área, nivel) + test < 300 ms" o "campo etiqueta_accesible" sí.
3. **Pedir pruebas trazables a los criterios** convierte la revisión en algo objetivo: si el test `ca2` pasa, el criterio se cumple.
4. **Iterar en pasos pequeños funciona mejor** que reescribir todo el prompt de golpe. Cada iteración atacó un hallazgo concreto de la revisión, y el prompt v2 es la suma de esos aprendizajes.
5. **La revisión humana sigue siendo indispensable.** Las pruebas generadas por la IA pueden pasar y aun así validar una regla mal interpretada, como "nivel = grado". Hay que leer el código contra la spec, no solo ejecutarlo.

## Autoevaluación frente a la rúbrica

| Criterio | Peso | Evidencia |
|---|---|---|
| Claridad del prompt inicial | 25 | [Prompt v1](02-prompt-inicial.md) completo y con tabla de alineación con la spec |
| Calidad del código generado | 30 | [Código](../../servicios/c4-motor-diagnostico/) modular, documentado, 36 pruebas en verde |
| Iteración y refinamiento | 25 | [6 iteraciones](04-validacion-y-refinamiento.md) y [prompt v2](05-prompt-refinado.md) con cambios marcados |
| Reflexión final | 20 | Este documento |

Anterior: [Validación con criterios](06-validacion-criterios.md) · [Volver al índice](README.md)
