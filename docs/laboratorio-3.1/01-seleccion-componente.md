# Parte A · Selección del componente

## Componente elegido: C4 Motor de diagnóstico

| Campo | Valor |
|---|---|
| Módulo | M2 Diagnóstico |
| Tipo | Servicio |
| Historia de usuario | HU-01: "Presentar un diagnóstico para conocer mi nivel en lectura y matemáticas" |
| Dependencias | C3 → **C4** → C15 (toma ítems del banco) · **C4** → C13 → C14 → C16 (guarda el resultado) |

## Por qué es crítico

1. **Es la puerta de entrada pedagógica.** El nivel que calcula C4 es el punto de partida de C6 (Motor de adaptación), de las alertas de C9 y del panel docente C8. Un nivel mal calculado afecta a toda la cadena.
2. **Concentra reglas de negocio verificables:** rachas, cierre, respuestas apresuradas y nivel inicial por grado. Esto permite evaluar con objetividad si el código generado cumple la spec.
3. **Tiene RNF exigentes:** < 300 ms con 2 GB de RAM, respuestas cifradas en el celular y compatibilidad con lector de pantalla. Son buenos para probar si la IA respeta restricciones no funcionales.
4. **Encaja con FastAPI:** es un servicio sin interfaz propia, así que la tecnología elegida cubre el componente completo.

## Especificación copiada del Laboratorio 2

> **C4 Motor de diagnóstico**
> Tipo: Servicio. HU: HU-01.
>
> **Propósito:** ubicar al estudiante en un nivel de 1 a 6 por área, alineado a PISA y Saber.
>
> **Entradas:** grado, área, respuesta y tiempo por ítem.
>
> **Salidas:** nivel por área y porcentaje de respuestas apresuradas.
>
> **Reglas:** inicia en el nivel del grado. Dos aciertos seguidos suben un nivel y dos errores lo bajan. Termina a los 20 ítems o con 4 ítems estables. Responder en menos del 30 por ciento del tiempo estimado marca la respuesta como apresurada.
>
> **Flujo:** 1. Inicia la prueba. 2. Muestra un ítem del nivel esperado. 3. Registra respuesta y tiempo. 4. Ajusta el nivel hasta el cierre. 5. Guarda el resultado en C13.
>
> **RNF:** siguiente ítem en menos de 300 ms con 2 GB de RAM. Respuestas correctas cifradas en el celular. Compatible con lector de pantalla.
>
> **Criterios de aceptación:**
> - Dado un estudiante de grado 7, cuando inicia lectura, entonces el primer ítem es del nivel de grado 7.
> - Dados dos aciertos seguidos, cuando envía el segundo, entonces el siguiente ítem sube un nivel.
> - Dado un ítem de 60 s estimados, cuando responde a los 15 s, entonces queda marcado como apresurado.

Siguiente: [Parte B · Prompt inicial](02-prompt-inicial.md)
