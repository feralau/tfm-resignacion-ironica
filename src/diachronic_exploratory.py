#!/usr/bin/env python3
"""
Análisis diacrónico exploratorio del subcorpus anotado.

Calcula la proporción de cada clase por año y por fase histórica sobre el
subcorpus anotado (1.200 mensajes, columna `año`). Reproduce las cifras
citadas en el TFM, §4.8 ("Análisis diacrónico e interpretación etnográfica").

ALCANCE Y LÍMITES (importante):
- Estas proporciones se calculan sobre el SUBCORPUS ANOTADO, que fue muestreado
  de forma estratificada (con sobremuestreo deliberado de clases minoritarias).
  Por tanto, NO son estimaciones poblacionales del hilo completo, sino indicios
  exploratorios sobre la muestra anotada con fiabilidad casi perfecta.
- El análisis confirmatorio sobre la totalidad del corpus (curva mensual +
  detección de puntos de cambio) queda fuera del alcance del TFM y se describe
  como línea futura (§6.3 del manuscrito).

Uso:
    python src/diachronic_exploratory.py
    python src/diachronic_exploratory.py --csv data/subcorpus/subcorpus_anotado_FINAL_anon.csv --out results/analysis/diachronic_exploratory.json
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

CLASSES = ["frustracion_explicita", "resignacion_ironica", "neutral", "otro"]

# Fases históricas definidas por el marco teórico del TFM (§2 y §4.8).
PHASES = {
    "fundacional_2010_2012": range(2010, 2013),
    "institucionalizacion_2013_2015": range(2013, 2016),
    "hegemonia_2016_2020": range(2016, 2021),
    "reciente_2021_2026": range(2021, 2027),
}


def load(csv_path):
    with open(csv_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def proportions(rows):
    """Proporción de cada clase y soporte total para un conjunto de filas."""
    n = len(rows)
    counts = defaultdict(int)
    for r in rows:
        counts[r["etiqueta_final"]] += 1
    props = {c: (counts[c] / n if n else 0.0) for c in CLASSES}
    return {"n": n, "counts": {c: counts[c] for c in CLASSES}, "proportions": props}


def by_year(rows):
    out = {}
    years = sorted({int(r["año"]) for r in rows})
    for y in years:
        out[str(y)] = proportions([r for r in rows if int(r["año"]) == y])
    return out


def by_phase(rows):
    out = {}
    for name, yrange in PHASES.items():
        out[name] = proportions([r for r in rows if int(r["año"]) in yrange])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="data/subcorpus/subcorpus_anotado_FINAL_anon.csv")
    ap.add_argument("--out", default="results/analysis/diachronic_exploratory.json")
    args = ap.parse_args()

    rows = load(args.csv)
    result = {
        "source": args.csv,
        "n_total": len(rows),
        "scope": "subcorpus anotado estratificado; proporciones exploratorias, no poblacionales",
        "by_phase": by_phase(rows),
        "by_year": by_year(rows),
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Resumen legible por consola (las cifras citadas en §4.8 del TFM).
    print(f"Subcorpus: {len(rows)} mensajes anotados\n")
    print("Proporción de resignacion_ironica (RI) y frustracion_explicita (FE) por fase:")
    for name, data in result["by_phase"].items():
        ri = data["proportions"]["resignacion_ironica"]
        fe = data["proportions"]["frustracion_explicita"]
        print(f"  {name:32s} n={data['n']:4d}  RI={ri:.3f}  FE={fe:.3f}")
    print(f"\nResultado escrito en {args.out}")


if __name__ == "__main__":
    main()
