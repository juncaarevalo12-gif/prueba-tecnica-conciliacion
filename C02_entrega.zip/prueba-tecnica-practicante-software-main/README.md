# Prueba técnica · Conciliación de facturas y pagos

Desarrollo individual: **40 minutos**. Defensa individual por Teams: **5 minutos**. Se permite IA e Internet durante el desarrollo, sin colaboración entre candidatos. La defensa se realiza sin asistentes de IA.

1. Lee `ENUNCIADO.md`: contiene todas las reglas que se evaluarán.
2. Desde esta carpeta comprueba `python --version` (en Windows también puedes usar `py`).
3. Ejecuta `python -m unittest discover -s tests -v`.
4. Ejecuta el programa con los datos de ejemplo:

```text
python -m conciliador --facturas datos/ejemplo/facturas.csv --pagos datos/ejemplo/pagos.csv --corte 2026-10-15 --salida salida
```

El programa heredado contiene defectos. Es normal que sus pruebas fallen. El ejemplo se ejecuta, pero produce resultados incorrectos; otras entradas inválidas pueden interrumpirlo. Debes corregir su comportamiento.

Trabaja en `conciliador/engine.py`; puedes modificar otros archivos y refactorizar. Conserva la interfaz `conciliar(facturas_path, pagos_path, fecha_corte)`, el comando anterior y las cabeceras de salida. Usa biblioteca estándar; no necesitas base de datos, interfaz gráfica, servicios o Docker.

Al terminar añade tus pruebas y completa `ENTREGA.md`. Comprime esta carpeta como `C01_entrega.zip`, sustituyendo C01 por el código que te indique el evaluador. No incluyas entornos virtuales, cachés ni claves. Envía el ZIP por el canal acordado antes del cierre; después, la defensa usa esa misma entrega.

Archivos principales:

- `conciliador/engine.py`: lectura, validación y cálculo heredados.
- `conciliador/__main__.py`: comando y escritura de resultados, ya implementados.
- `tests/test_publicos.py`: siete comprobaciones de ejemplo; puedes añadir otras.
- `datos/ejemplo/`: entradas ficticias y resultado completo esperado para corte 2026-10-15.
- `ENUNCIADO.md`: contrato y prioridades.
- `ENTREGA.md`: notas de tu solución y uso de IA.

Las pruebas públicas son orientativas y no otorgan puntos por sí solas. El evaluador usará otros datos con las mismas reglas publicadas. No se espera que completes necesariamente todos los niveles; prioriza una solución que puedas explicar y probar.
