import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
import re

FACTURAS = ("factura_id", "cliente_id", "fecha_vencimiento", "importe")
PAGOS = ("pago_id", "factura_id", "cliente_id", "fecha_pago", "importe")
RESUMEN = ("factura_id", "cliente_id", "fecha_vencimiento", "importe", "pagado", "saldo", "estado", "vencida")
INCIDENCIAS = ("archivo", "fila", "codigo", "referencia")

PATRON_IMPORTE = re.compile(r"^\d{1,14}([.,]\d{1,2})?$")


def normalizar(valor):
    if not isinstance(valor, str):
        return ""
    return valor.strip().upper()


def dinero(valor):
    if not isinstance(valor, str):
        raise ValueError("Importe inválido")
    texto = valor.strip()
    if not PATRON_IMPORTE.match(texto):
        raise ValueError("Importe inválido")
    monto = Decimal(texto.replace(",", ".")).quantize(Decimal("0.01"))
    if monto <= Decimal("0.00"):
        raise ValueError("Importe debe ser positivo")
    return monto


def fecha(valor):
    if not isinstance(valor, str):
        raise ValueError("Fecha inválida")
    texto = valor.strip()
    if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":
        raise ValueError("Fecha inválida")
    return date.fromisoformat(texto)


def leer_csv(ruta, columnas):
    with Path(ruta).open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.reader(archivo)
        cabecera = None
        for fila in lector:
            if not fila or (len(fila) == 1 and fila[0].strip() == ""):
                continue
            cabecera = [c.strip() for c in fila]
            break
        if (
            cabecera is None
            or any(c == "" for c in cabecera)
            or len(cabecera) != len(set(cabecera))
            or not set(columnas).issubset(cabecera)
        ):
            raise ValueError("Cabecera inválida: " + Path(ruta).name)
        num_cols = len(cabecera)
        for fila in lector:
            if not fila or (len(fila) == 1 and fila[0].strip() == ""):
                continue
            datos = {cabecera[i]: (fila[i] if i < len(fila) else None) for i in range(num_cols)}
            datos["_exceso_cols"] = len(fila) > num_cols
            yield lector.line_num, datos


def conciliar(facturas_path, pagos_path, fecha_corte):
    corte = fecha(fecha_corte)
    filas_facturas = list(leer_csv(facturas_path, FACTURAS))
    filas_pagos = list(leer_csv(pagos_path, PAGOS))

    facturas = {}
    incidencias = []

    for numero, fila in filas_facturas:
        factura_id = normalizar(fila.get("factura_id"))
        cliente_id = normalizar(fila.get("cliente_id"))
        if (
            fila.get("_exceso_cols")
            or any(fila.get(col) is None for col in FACTURAS)
            or not factura_id
            or not cliente_id
        ):
            incidencias.append(dict(archivo="facturas", fila=str(numero), codigo="FILA_INVALIDA", referencia=factura_id))
            continue
        try:
            vencimiento = fecha(fila.get("fecha_vencimiento"))
            importe = dinero(fila.get("importe"))
        except ValueError:
            incidencias.append(dict(archivo="facturas", fila=str(numero), codigo="FILA_INVALIDA", referencia=factura_id))
            continue

        if factura_id in facturas:
            incidencias.append(dict(archivo="facturas", fila=str(numero), codigo="FACTURA_DUPLICADA", referencia=factura_id))
            continue

        facturas[factura_id] = dict(
            cliente=cliente_id,
            vencimiento=vencimiento,
            importe=importe,
            pagado=Decimal("0.00")
        )

    pagos_vistos = set()

    for numero, fila in filas_pagos:
        pago_id = normalizar(fila.get("pago_id"))
        factura_id = normalizar(fila.get("factura_id"))
        cliente_id = normalizar(fila.get("cliente_id"))
        if (
            fila.get("_exceso_cols")
            or any(fila.get(col) is None for col in PAGOS)
            or not pago_id
            or not factura_id
            or not cliente_id
        ):
            incidencias.append(dict(archivo="pagos", fila=str(numero), codigo="FILA_INVALIDA", referencia=pago_id))
            continue
        try:
            fecha_pago = fecha(fila.get("fecha_pago"))
            importe = dinero(fila.get("importe"))
        except ValueError:
            incidencias.append(dict(archivo="pagos", fila=str(numero), codigo="FILA_INVALIDA", referencia=pago_id))
            continue

        if pago_id in pagos_vistos:
            incidencias.append(dict(archivo="pagos", fila=str(numero), codigo="PAGO_DUPLICADO", referencia=pago_id))
            continue
        pagos_vistos.add(pago_id)

        if fecha_pago > corte:
            incidencias.append(dict(archivo="pagos", fila=str(numero), codigo="PAGO_FUERA_CORTE", referencia=pago_id))
            continue

        if factura_id not in facturas:
            incidencias.append(dict(archivo="pagos", fila=str(numero), codigo="FACTURA_NO_EXISTE", referencia=pago_id))
            continue

        if facturas[factura_id]["cliente"] != cliente_id:
            incidencias.append(dict(archivo="pagos", fila=str(numero), codigo="CLIENTE_NO_COINCIDE", referencia=pago_id))
            continue

        facturas[factura_id]["pagado"] += importe

    resumen = []
    total_importe = Decimal("0.00")
    total_pagado = Decimal("0.00")

    for factura_id, factura in sorted(facturas.items()):
        importe = factura["importe"]
        pagado = factura["pagado"]
        saldo = importe - pagado

        if pagado == Decimal("0.00"):
            estado = "PENDIENTE"
        elif saldo > Decimal("0.00"):
            estado = "PARCIAL"
        elif saldo == Decimal("0.00"):
            estado = "PAGADA"
        else:
            estado = "SOBREPAGADA"

        vencida = "SI" if (saldo > Decimal("0.00") and factura["vencimiento"] < corte) else "NO"

        resumen.append(dict(
            factura_id=factura_id,
            cliente_id=factura["cliente"],
            fecha_vencimiento=factura["vencimiento"].isoformat(),
            importe=f"{importe:.2f}",
            pagado=f"{pagado:.2f}",
            saldo=f"{saldo:.2f}",
            estado=estado,
            vencida=vencida
        ))
        total_importe += importe
        total_pagado += pagado

    total_saldo = total_importe - total_pagado

    return dict(
        resumen=resumen,
        incidencias=incidencias,
        totales=dict(
            facturas_validas=len(resumen),
            importe=f"{total_importe:.2f}",
            pagado=f"{total_pagado:.2f}",
            saldo=f"{total_saldo:.2f}",
            incidencias=len(incidencias)
        )
    )