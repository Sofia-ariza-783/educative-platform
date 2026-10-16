# Parte D · Validación con criterios de aceptación

Ejecución sobre la versión final, el 15 de octubre de 2026:

```bash
cd servicios/c4-motor-diagnostico
pytest -q
# 36 passed in 0.48s
```

## Criterios de aceptación de la spec

| # | Criterio | Prueba | Estado |
|---|---|---|---|
| CA1 | Dado un estudiante de grado 7, cuando inicia lectura, entonces el primer ítem es del nivel de grado 7. | `test_ca1_grado_7_lectura_inicia_en_nivel_del_grado` | ✅ Cumple |
| CA2 | Dados dos aciertos seguidos, cuando envía el segundo, entonces el siguiente ítem sube un nivel. | `test_ca2_dos_aciertos_seguidos_suben_un_nivel` | ✅ Cumple |
| CA3 | Dado un ítem de 60 s estimados, cuando responde a los 15 s, entonces queda marcado como apresurado. | `test_ca3_respuesta_a_15s_de_60s_estimados_es_apresurada` | ✅ Cumple |

## Reglas de negocio y RNF

| Regla / RNF | Evidencia | Estado                                  |
|---|---|-----------------------------------------|
| Dos errores bajan un nivel | `test_dos_errores_seguidos_bajan_un_nivel` | ✅ Cumple                                |
| Termina con 4 ítems estables y guarda en C13 | `test_cierra_con_4_items_estables_y_guarda_en_c13` | ✅ Cumple                                |
| Termina a los 20 ítems | `test_cierra_a_los_20_items_si_el_nivel_no_se_estabiliza` | ✅ Cumple                                |
| Salida: porcentaje de apresuradas | `test_porcentaje_de_apresuradas_en_el_resultado` | ✅ Cumple                                |
| Siguiente ítem < 300 ms | `test_siguiente_item_en_menos_de_300_ms_con_banco_grande` (6 000 ítems) | ✅ Cumple en PC de desarrollo            |
| Respuestas correctas cifradas | `test_el_banco_no_guarda_respuestas_en_texto_plano`, `test_el_item_publico_no_expone_la_respuesta` | ✅ Cumple con huella HMAC                |
| Compatible con lector de pantalla | `test_el_item_incluye_etiqueta_para_lector_de_pantalla` | El servicio entrega el texto accesible  |

## Ajustes pendientes

1. **Validar la tabla grado → nivel** (6→2 … 9→5) con el equipo pedagógico. Es un supuesto, porque la spec no la define. Se cambia en `app/config.py` sin tocar la lógica.
2. **Persistir las sesiones en curso** en C13. Hoy viven en memoria y se pierden si se cierra la app a mitad de la prueba.
3. **Medir el rendimiento en un dispositivo real** de 2 GB de RAM.
4. **Aclarar en la spec** si las respuestas apresuradas deben contar para subir de nivel en el diagnóstico. C6 lo excluye, pero C4 no lo dice. La implementación actual sigue la spec de C4 literalmente: sí cuentan.

Anterior: [Prompt refinado](05-prompt-refinado.md) · Siguiente: [Reflexión](07-reflexion.md)
