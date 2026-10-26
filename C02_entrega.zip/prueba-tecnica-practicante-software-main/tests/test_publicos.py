import json
from pathlib import Path
import tempfile
import unittest
from conciliador.engine import conciliar, normalizar, dinero

ROOT = Path(__file__).resolve().parents[1]


class PruebasPublicas(unittest.TestCase):
    def setUp(self):
        self.datos = ROOT / "datos/ejemplo"

    def resultado(self):
        return conciliar(self.datos / "facturas.csv", self.datos / "pagos.csv", "2026-10-15")

    def test_01_identificadores(self):
        self.assertEqual(normalizar(" f100 "), "F100")

    def test_02_importe_coma(self):
        self.assertEqual(str(dinero("12,50")), "12.50")

    def test_03_acumula_pagos(self):
        self.assertEqual(self.resultado()["resumen"][0]["pagado"], "60.00")

    def test_04_sobrepago(self):
        self.assertEqual(self.resultado()["resumen"][3]["estado"], "SOBREPAGADA")

    def test_05_no_vence_el_mismo_dia(self):
        self.assertEqual(self.resultado()["resumen"][4]["vencida"], "NO")

    def test_06_incidencias(self):
        self.assertEqual(len(self.resultado()["incidencias"]), 7)

    def test_07_ejemplo_completo(self):
        esperado = json.loads((self.datos / "esperado.json").read_text(encoding="utf-8"))
        self.assertEqual(self.resultado(), esperado)

    def test_08_archivos_vacios_y_orden_columnas(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp)
            f_csv = ruta / "facturas.csv"
            p_csv = ruta / "pagos.csv"
            f_csv.write_text("importe,cliente_id,factura_id,extra,fecha_vencimiento\n", encoding="utf-8")
            p_csv.write_text("fecha_pago,importe,cliente_id,factura_id,pago_id\n", encoding="utf-8")
            res = conciliar(f_csv, p_csv, "2026-10-15")
            self.assertEqual(res["resumen"], [])
            self.assertEqual(res["incidencias"], [])
            self.assertEqual(res["totales"], {
                "facturas_validas": 0,
                "importe": "0.00",
                "pagado": "0.00",
                "saldo": "0.00",
                "incidencias": 0
            })

    def test_09_reserva_id_y_prioridad_incidencias(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp)
            f_csv = ruta / "facturas.csv"
            p_csv = ruta / "pagos.csv"
            f_csv.write_text(
                "factura_id,cliente_id,fecha_vencimiento,importe\n"
                "f01,c01,2026-10-01,0\n"
                "F01,C01,2026-10-01,100,50\n"
                "F01,C01,2026-10-01,50.25\n",
                encoding="utf-8"
            )
            p_csv.write_text(
                'pago_id,factura_id,cliente_id,fecha_pago,importe\n'
                'P01,F01,C01,2026-10-20,10.00\n'
                'p01,F01,C01,2026-10-05,10.00\n'
                'P02,F01,C01,2026-10-05,"25,10"\n',
                encoding="utf-8"
            )
            res = conciliar(f_csv, p_csv, "2026-10-15")
            self.assertEqual(len(res["resumen"]), 1)
            self.assertEqual(res["resumen"][0]["importe"], "50.25")
            self.assertEqual(res["resumen"][0]["pagado"], "25.10")
            self.assertEqual(res["resumen"][0]["saldo"], "25.15")
            codigos = [(i["archivo"], i["fila"], i["codigo"], i["referencia"]) for i in res["incidencias"]]
            self.assertEqual(codigos, [
                ("facturas", "2", "FILA_INVALIDA", "F01"),
                ("facturas", "3", "FILA_INVALIDA", "F01"),
                ("pagos", "2", "PAGO_FUERA_CORTE", "P01"),
                ("pagos", "3", "PAGO_DUPLICADO", "P01")
            ])

    def test_10_errores_cabecera_y_corte(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp)
            f_csv = ruta / "facturas.csv"
            p_csv = ruta / "pagos.csv"
            f_csv.write_text("factura_id,cliente_id,importe\n", encoding="utf-8")
            p_csv.write_text("pago_id,factura_id,cliente_id,fecha_pago,importe\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                conciliar(f_csv, p_csv, "2026-10-15")
            f_csv.write_text("factura_id,cliente_id,fecha_vencimiento,importe\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                conciliar(f_csv, p_csv, "15-10-2026")


if __name__ == "__main__":
    unittest.main()