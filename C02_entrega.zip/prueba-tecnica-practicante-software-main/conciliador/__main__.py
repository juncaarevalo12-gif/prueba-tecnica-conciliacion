"""Interfaz de línea de comandos compartida con el proyecto inicial."""
import argparse
import csv
import json
import sys
from pathlib import Path
from conciliador.engine import conciliar, RESUMEN, INCIDENCIAS


def main():
    parser = argparse.ArgumentParser(description="Concilia facturas y pagos ficticios")
    parser.add_argument("--facturas", required=True)
    parser.add_argument("--pagos", required=True)
    parser.add_argument("--corte", required=True)
    parser.add_argument("--salida", required=True)
    args = parser.parse_args()
    try:
        resultado = conciliar(args.facturas, args.pagos, args.corte)
        destino = Path(args.salida)
        destino.mkdir(parents=True, exist_ok=True)
        for nombre, campos in (("resumen", RESUMEN), ("incidencias", INCIDENCIAS)):
            with (destino / (nombre + ".csv")).open("w", encoding="utf-8", newline="") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=campos)
                escritor.writeheader()
                escritor.writerows(resultado[nombre])
        (destino / "totales.json").write_text(json.dumps(resultado["totales"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ValueError, OSError, csv.Error) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
