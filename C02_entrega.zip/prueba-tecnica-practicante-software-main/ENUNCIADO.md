# Enunciado · Conciliación de facturas y pagos

## Situación

Una organización ficticia necesita revisar qué facturas siguen pendientes a una fecha de corte. Un proceso Python existente lee dos CSV, pero sus resultados no son confiables. Debes repararlo, completar las validaciones y entregar evidencia de tus decisiones.

Tienes 40 minutos de desarrollo individual, con IA e Internet permitidos. Después tendrás 5 minutos para demostrar y explicar tu entrega por Teams, sin asistentes generativos ni autocompletado con IA; puedes consultar el enunciado y tus notas entregadas. No se valora escribir mucho código ni ocultar el uso de IA. Se valora resolver, verificar y comprender.

## Prioridades y tiempo orientativo

- **Nivel A · Funcional (aprox. 15 min):** revisar el proyecto, corregir acumulación de pagos, estados, precisión, saldo y vencimiento. Producir las salidas acordadas.
- **Nivel B · Datos problemáticos (aprox. 10 min):** normalizar identificadores, controlar duplicados, pagos sin factura, cliente incorrecto, fechas e importes inválidos y corte.
- **Nivel C · Confiabilidad (aprox. 10 min):** entradas vacías con cabecera, repetición determinista, errores de archivo/cabecera/corte y pruebas propias.
- **Cierre (aprox. 5 min):** completar `ENTREGA.md`, comprimir y entregar. Si falta algo, decláralo.

Son prioridades, no etapas bloqueantes. Puedes implementarlas en otro orden. Todos los niveles pueden sumar puntos. No hay requisitos sorpresa en los datos reservados.

## Entradas

`facturas.csv` tiene las columnas `factura_id,cliente_id,fecha_vencimiento,importe`.

`pagos.csv` tiene las columnas `pago_id,factura_id,cliente_id,fecha_pago,importe`.

Reglas de formato:

1. CSV separado por coma, con cabecera, codificado en UTF-8 con o sin BOM. Puede venir en orden de columnas diferente. Las columnas adicionales con nombre se ignoran. No cambies los archivos fuente.
2. Una coma decimal se escribe entre comillas: `"12,50"`. Se aceptan `12`, `12.5`, `12.50` y `12,50`, con espacios exteriores opcionales. No se aceptan separadores de miles, signos, notación científica, NaN, infinitos, más de dos decimales, cero, negativos ni texto vacío. No redondees una entrada inválida para aceptarla.
3. Dinero exacto: usa `decimal.Decimal` o centavos enteros; evita `float`. Las salidas monetarias son cadenas con punto y exactamente dos decimales, incluidos ceros. No hay tolerancia monetaria. Los datos de evaluación tienen hasta 14 dígitos enteros por importe y como máximo 10.000 filas por archivo.
4. Identificadores: quita espacios exteriores y convierte a mayúsculas. Los espacios interiores y ceros iniciales se conservan. No pueden quedar vacíos. `f001` y ` F001 ` representan el mismo ID; `F1` y `F001` son distintos. `factura_id` es globalmente único, incluso entre clientes; `pago_id` también es globalmente único.
5. Fechas: cadenas `AAAA-MM-DD` estrictas y fechas de calendario reales, permitiendo espacios exteriores. El corte usa ese mismo formato. Todas son fechas sin hora. Se permiten fechas históricas y de vencimiento posteriores al corte.
6. Una fila con identificador vacío, importe/fecha inválidos, alguna celda requerida ausente o celdas de más respecto de la cabecera genera `FILA_INVALIDA` y se descarta. Una fila estructuralmente inválida **no reserva** su identificador.
7. Una cabecera sin alguna columna requerida, con nombres duplicados, o un archivo sin cabecera es error del archivo completo. Un CSV con solo cabecera es válido. Las líneas vacías se ignoran; para `fila` cuenta la posición física del archivo incluyendo cabecera (primera fila de datos: 2). No habrá celdas con saltos de línea ni CSV con comillas rotas.

## Reglas de negocio y orden de validación

Procesa primero todas las facturas, luego todos los pagos. Recorre las filas de cada archivo en su orden original. Una fila descartada genera exactamente una incidencia, según la primera regla aplicable en el orden siguiente.

**Facturas:** valida estructura y valores; después comprueba duplicado. Conserva la primera factura estructuralmente válida de cada ID normalizado. Toda aparición válida posterior genera `FACTURA_DUPLICADA` y no reemplaza el registro. Si la aparición posterior es inválida, genera `FILA_INVALIDA`.

**Pagos**, en este orden:

1. Valida estructura, identificadores, fecha e importe. Si falla algo: `FILA_INVALIDA`.
2. Si ya apareció ese `pago_id` en una fila estructuralmente válida: `PAGO_DUPLICADO`. Descártala. Si aún no apareció, reserva el ID **antes de aplicar las siguientes reglas**.
3. Si `fecha_pago > fecha_corte`: `PAGO_FUERA_CORTE`. El día del corte sí se incluye.
4. Si la factura no existe entre las facturas válidas conservadas: `FACTURA_NO_EXISTE`.
5. Si el cliente del pago no coincide con el de esa factura: `CLIENTE_NO_COINCIDE`.
6. Si pasa todo, suma el importe al pagado de esa factura.

Un pago fuera de corte, huérfano o de cliente incorrecto reserva su ID: una fila válida posterior con ese mismo ID es duplicada, aunque corrija el error. Esta política hace trazable la primera aparición; no intentes corregir entradas automáticamente. No distribuyas pagos entre facturas, no uses FIFO y no concilies por cliente solamente.

Para cada factura válida:

- `pagado`: suma exacta de los pagos aceptados; cero si no hay ninguno.
- `saldo = importe - pagado`. Puede ser negativo y no se recorta a cero.
- `estado`: `PENDIENTE` si pagado es cero; `PARCIAL` si pagado es positivo y saldo positivo; `PAGADA` si saldo es cero; `SOBREPAGADA` si saldo es negativo.
- `vencida`: `SI` únicamente si saldo es positivo y `fecha_vencimiento < fecha_corte`; en cualquier otro caso, `NO`. El vencimiento en la propia fecha de corte no cuenta como vencido.

## Contrato de salida

Conserva `conciliador.engine.conciliar(facturas_path, pagos_path, fecha_corte)`; recibe rutas `str` o `Path` y corte `str`. Devuelve un diccionario con exactamente estas tres claves:

- `resumen`: lista de diccionarios, una fila por factura válida, ordenada ascendentemente por `factura_id` normalizado. Claves: `factura_id,cliente_id,fecha_vencimiento,importe,pagado,saldo,estado,vencida`. Todos los valores son cadenas.
- `incidencias`: lista de diccionarios con claves `archivo,fila,codigo,referencia`. Todos los valores son cadenas. `archivo` vale `facturas` o `pagos`, sin ruta ni extensión; `fila` es el número de fila como texto; `referencia` es el ID normalizado de factura o de pago de esa fila, o cadena vacía si falta. Conserva el orden de detección: incidencias de facturas primero, luego pagos. No se requiere una descripción adicional.
- `totales`: diccionario con `facturas_validas` e `incidencias` como enteros, y `importe`, `pagado`, `saldo` como cadenas monetarias. Los importes totalizan exclusivamente las facturas válidas y pagos aceptados. El saldo total es la suma algebraica de todos los saldos, incluidos los negativos. `incidencias` cuenta todas las filas descartadas.

El comando documentado en `README.md` debe guardar `resumen.csv`, `incidencias.csv` y `totales.json` en la carpeta indicada. Los CSV conservan el orden de columnas anterior, tienen cabecera incluso si no hay registros y usan UTF-8. El comando debe terminar con código 0 cuando finaliza, aun si hay incidencias de filas.

El mismo conjunto de entradas y corte debe producir la misma salida. Si repites el comando en la misma carpeta, reemplaza los tres archivos; no anexes filas ni dupliques cabeceras. No conserves estado entre llamadas a `conciliar`.

Archivo inexistente/ilegible, cabecera inválida o corte inválido: la función puede propagar `OSError` o `ValueError`. El comando debe mostrar un mensaje por la salida de error y terminar con código 2. No debe crear ni reemplazar ninguno de los tres archivos de resultados cuando falla la validación de entradas. El código de escritura ya ofrece ese comportamiento si la función calcula y valida antes de devolver. No se exige escritura atómica frente a fallos del disco.

## Ejemplo comprobable

Con `datos/ejemplo` y corte `2026-10-15`:

- F100 tiene importe 100.00, pagos aceptados 20.00 + 40.00 = 60.00, saldo 40.00, estado PARCIAL y vencida SI.
- F200 queda PAGADA. F400 queda SOBREPAGADA con saldo -20.00.
- F500 vence el día del corte: vencida NO.
- Totales: 6 facturas, importe 470.00, pagado 360.00, saldo 110.00 y 7 incidencias.

El resultado completo está en `datos/ejemplo/esperado.json`. Este archivo sirve para comparar; el programa debe calcular desde los CSV, nunca copiar resultados predefinidos.

## Entrega, IA y evaluación

Entrega código ejecutable, al menos dos pruebas propias de escenarios diferentes y `ENTREGA.md` completo. No borres ni debilites las pruebas públicas para hacerlas pasar. Puedes agregar pruebas, archivos auxiliares y comentarios útiles. Las pruebas propias deben usar entradas y expectativas verificables, preferiblemente temporales.

Puedes usar IA para diagnosticar, implementar y escribir pruebas. Declara brevemente herramienta, tareas asistidas y cómo verificaste el resultado. No se piden conversaciones completas, cuentas, datos privados ni historial de navegación. Si no usaste IA, indícalo. El uso de IA no añade ni resta puntos.

Puntaje total: **55 puntos** de validación automática con otros CSV bajo este contrato; **10** por pruebas propias; **5** por entrega y notas; **30** por defensa. La automatización reparte 5 puntos por cada familia: estados/acumulación, normalización/CSV, duplicados, filas inválidas, relaciones factura-cliente, corte, vencimiento, centavos, archivos vacíos, combinación de reglas y comando/repetición/errores. En las diez familias de datos se asignan 3 puntos al resumen, 1 a incidencias y 1 a totales; cada bloque se aprueba completo. En comando: 3 por salida correcta y repetible, 1 por cabecera inválida y 1 por corte inválido.

La defensa verifica: explicación del flujo y dinero (6), seguimiento de un caso (6), explicación de una prueba propia (6), cambio pequeño con verificación (6) y evaluación crítica del trabajo/IA (6). No se evalúan conocimientos corporativos ni apariencia de una interfaz. Documenta los pendientes: una solución parcial que entiendes puede obtener puntos.
