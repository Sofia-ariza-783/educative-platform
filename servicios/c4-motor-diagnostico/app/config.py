"""Parámetros de negocio del Motor de diagnóstico (C4).

Todas las reglas numéricas de la especificación viven aquí para que el equipo
pedagógico pueda ajustarlas sin tocar la lógica del motor.
"""

# Escala de niveles alineada a PISA y Saber.
NIVEL_MIN = 1
NIVEL_MAX = 6

# Grados atendidos por LeeCuenta.
GRADO_MIN = 6
GRADO_MAX = 9

# Nivel esperado (punto de partida) para cada grado.
# Supuesto a validar con el equipo pedagógico: grado 6 -> nivel 2 ... grado 9 -> nivel 5.
# Es coherente con la alerta de C8 ("dos niveles por debajo de su grado").
NIVEL_ESPERADO_POR_GRADO = {6: 2, 7: 3, 8: 4, 9: 5}

# Reglas de cierre de la prueba.
MAX_ITEMS = 20
ITEMS_ESTABLES_PARA_CERRAR = 4

# Rachas que provocan cambio de nivel.
ACIERTOS_PARA_SUBIR = 2
ERRORES_PARA_BAJAR = 2

# Una respuesta dada en menos de este porcentaje del tiempo estimado es apresurada.
UMBRAL_APRESURADA = 0.30

# Opciones de respuesta admitidas por ítem (selección múltiple).
CLAVES_OPCIONES = ("A", "B", "C", "D")

# Variable de entorno con la clave usada para proteger las respuestas correctas.
VARIABLE_CLAVE_ITEMS = "LEECUENTA_CLAVE_ITEMS"
