# Parte B · Prompt inicial (v1)

Es la plantilla 3.1 completada con la especificación de C4 del Laboratorio 2, sin agregar información. Este es el prompt que se pegó en Vibe Coding.

```text
Quiero que generes el código de un componente llamado: C4 Motor de diagnóstico
Tipo: Servicio
Lenguaje/Framework preferido: Python con FastAPI

Especificación del componente:
- Propósito: ubicar al estudiante en un nivel de 1 a 6 por área (lectura y
  matemáticas), alineado a PISA y Saber. Forma parte de LeeCuenta, una app móvil
  de práctica adaptativa para estudiantes de grados 6 a 9 de colegios oficiales,
  que funciona sin conexión.
- Entradas: grado, área, respuesta y tiempo por ítem.
- Salidas: nivel por área y porcentaje de respuestas apresuradas.
- Reglas de negocio:
  * Inicia en el nivel del grado.
  * Dos aciertos seguidos suben un nivel y dos errores lo bajan.
  * Termina a los 20 ítems o con 4 ítems estables.
  * Responder en menos del 30 % del tiempo estimado marca la respuesta como
    apresurada.
- Flujo principal (máx. 5 pasos):
  1. Inicia la prueba.
  2. Muestra un ítem del nivel esperado.
  3. Registra respuesta y tiempo.
  4. Ajusta el nivel hasta el cierre.
  5. Guarda el resultado en el almacenamiento local (C13).
- RNF clave: siguiente ítem en menos de 300 ms con 2 GB de RAM; respuestas
  correctas cifradas en el celular; compatible con lector de pantalla.
- Criterios de aceptación:
  * Dado un estudiante de grado 7, cuando inicia lectura, entonces el primer
    ítem es del nivel de grado 7.
  * Dados dos aciertos seguidos, cuando envía el segundo, entonces el siguiente
    ítem sube un nivel.
  * Dado un ítem de 60 s estimados, cuando responde a los 15 s, entonces queda
    marcado como apresurado.

Requerimientos adicionales para el código:
- Código modular y comentado.
- Buenas prácticas de Python y FastAPI.
- Pruebas unitarias básicas incluidas.
- Documentación mínima (README corto con instrucciones de ejecución).
```

## Alineación con la especificación

| Campo de la plantilla | Fuente en la spec C4 | ¿Completo? |
|---|---|---|
| Nombre, tipo, framework | Mapa de componentes + tecnología del proyecto | Sí |
| Propósito | Propósito + contexto del producto | Sí |
| Entradas / Salidas | Entradas / Salidas | Sí |
| Reglas de negocio | Reglas (4) | Sí |
| Flujo | Flujo (5 pasos) | Sí |
| RNF | RNF (3) | Sí |
| Criterios de aceptación | Criterios (3) | Sí |

Anterior: [Parte A](01-seleccion-componente.md) · Siguiente: [Código generado](03-codigo-generado.md)
