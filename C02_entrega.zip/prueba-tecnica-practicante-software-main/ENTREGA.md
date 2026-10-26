# Notas de entrega

Código de candidato: C02

Versión de Python usada: Python 3.13.1

## Qué funciona

- Nivel A: Funciona completo. Acumulación exacta de pagos aceptados por factura (`+=`), cálculo de saldos (incluyendo negativos), asignación de los cuatro estados (`PENDIENTE`, `PARCIAL`, `PAGADA`, `SOBREPAGADA`), evaluación de vencimiento estricta (`saldo > 0` y `fecha_vencimiento < fecha_corte`) y generación de `resumen`, `incidencias` y `totales`.
- Nivel B: Funciona completo. Normalización de identificadores (`.strip().upper()`), control de duplicados en facturas y pagos conservando la primera aparición válida, detección de pagos fuera de corte (`PAGO_FUERA_CORTE`), pagos a facturas inexistentes (`FACTURA_NO_EXISTE`), clientes que no coinciden (`CLIENTE_NO_COINCIDE`) y validación estricta de importes (con punto o coma decimal) y fechas ISO (`AAAA-MM-DD`).
- Nivel C: Funciona completo. Soporte para archivos vacíos con solo cabecera, columnas en distinto orden o columnas adicionales ignoradas, líneas en blanco ignoradas conservando el número de línea físico (`line_num`), ejecución determinista sin estado residual entre llamadas, validación previa de ambos archivos antes de procesar para propagar `ValueError`/`OSError` sin dejar archivos parciales, y 3 pruebas unitarias propias añadidas.

## Cómo ejecutar y verificar

Comandos utilizados y resultados observados (incluye cantidad de pruebas aprobadas/fallidas):

1. Ejecución de pruebas unitarias:
   `python -m unittest discover -s tests -v`
   Resultado observado: `Ran 10 tests in 0.151s - OK` (10 pruebas aprobadas, 0 fallidas: las 7 pruebas públicas originales más 3 pruebas propias).

2. Ejecución del programa con los datos de ejemplo:
   `python -m conciliador --facturas datos/ejemplo/facturas.csv --pagos datos/ejemplo/pagos.csv --corte 2026-10-15 --salida salida`
   Resultado observado: Terminación con código 0 y creación correcta de `salida/resumen.csv`, `salida/incidencias.csv` y `salida/totales.json`, coincidiendo con `datos/ejemplo/esperado.json` (6 facturas válidas, importe 470.00, pagado 360.00, saldo 110.00 y 7 incidencias).

## Decisiones

Explica dos decisiones: representación del dinero y orden de validación/deduplicación.

1. Representación del dinero:
   Se reemplazó `float` por `decimal.Decimal` junto con una expresión regular previa (`^\d{1,14}([.,]\d{1,2})?$`). Esto evita errores de precisión binaria en punto flotante al sumar centavos, permite aceptar tanto punto como coma decimal (reemplazando `,` por `.` antes de instanciar `Decimal`), cuantiza exactamente a dos decimales (`0.01`) y rechaza explícitamente ceros, negativos, signos (`+`/`-`), más de dos decimales, separadores de miles o valores no numéricos sin redondear entradas inválidas.

2. Orden de validación y deduplicación:
   Tanto en facturas como en pagos se valida primero la estructura de la fila (que no existan celdas de más respecto a la cabecera ni celdas requeridas ausentes) y el formato de identificadores, fechas e importes. Si algo falla, se registra `FILA_INVALIDA` y se descarta la fila antes de tocar los registros de IDs vistos, garantizando que una fila inválida nunca reserve su identificador. En cambio, en los pagos estructuralmente válidos, se verifica si el `pago_id` ya está en el conjunto `pagos_vistos`; si no está, se reserva inmediatamente en `pagos_vistos` antes de validar fecha de corte, existencia de factura o coincidencia de cliente. Así, cualquier pago posterior con ese mismo ID se marca como `PAGO_DUPLICADO` aunque el primero haya sido descartado por negocio.

## Pruebas propias

Indica al menos dos escenarios, qué fallo detectan y dónde están las pruebas.

Las pruebas se encuentran en `tests/test_publicos.py` dentro de la clase `PruebasPublicas`:

1. `test_08_archivos_vacios_y_orden_columnas`:
   Crea archivos CSV temporales que contienen únicamente la cabecera, con las columnas requeridas en orden distinto al habitual y una columna extra. Detecta fallos si el lector asume posiciones fijas de columnas, si falla ante columnas adicionales o si no devuelve totales en `"0.00"` cuando no hay filas de datos.

2. `test_09_reserva_id_y_prioridad_incidencias`:
   Evalúa la interacción entre filas inválidas y reserva de identificadores. En facturas introduce primero filas inválidas para `F01` (importe `0` y exceso de columnas por coma sin comillas) seguidas de una fila válida para `F01`, detectando si una fila inválida bloquea erróneamente un ID posterior. En pagos introduce `P01` fuera de la fecha de corte y luego repite `p01` en minúscula dentro del corte, detectando si el sistema olvida reservar el ID de un pago rechazado por fecha de corte.

3. `test_10_errores_cabecera_y_corte`:
   Verifica que ante una cabecera incompleta (falta `fecha_vencimiento`) o una fecha de corte con formato inválido (`15-10-2026`) la función propague `ValueError`.

## Uso de IA

Herramienta(s), tareas asistidas, una sugerencia revisada y cómo la comprobaste. O indica que no la usaste.

- Herramienta: Gemini.
- Tareas asistidas: Análisis de las reglas de validación del enunciado, refactorización de `conciliador/engine.py` y estructura de pruebas adicionales en `tests/test_publicos.py`.
- Sugerencia revisada y comprobación: Inicialmente se revisó el comportamiento de lectura del CSV para no usar `DictReader` de forma ingenua ni ignorar filas que contienen únicamente comas vacías (`,,,`). Se ajustó `leer_csv` usando `csv.reader` para ignorar únicamente líneas en blanco reales (`len(fila) == 1` vacía) manteniendo el número físico de fila (`line_num`) y detectando explícitamente cuando una fila tiene más celdas que la cabecera (`_exceso_cols`) o celdas requeridas ausentes. Se comprobó ejecutando `python -m unittest discover -s tests -v` (10/10 tests en OK) y comparando la salida contra `datos/ejemplo/esperado.json`.

## Pendientes y limitaciones

Qué falta, cómo lo abordarías y qué verificaste realmente. No declares pruebas ejecutadas si solo leíste el código.

- Todos los requerimientos de los niveles A, B y C fueron implementados y verificados.
- Verificación realizada: Se ejecutaron en consola tanto la suite de 10 pruebas unitarias con `unittest` como el comando CLI completo sobre `datos/ejemplo`, verificando los archivos generados.
- Limitación conocida (acorde al enunciado): Los archivos se cargan en memoria al inicio de `conciliar` para validar ambas cabeceras antes de procesar (adecuado para el límite de 10.000 filas del contrato); si en el futuro se requiriera procesar archivos de millones de filas, se podría separar la validación de cabeceras en un paso previo y luego iterar en streaming con generadores.