#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baselines.py — Líneas base de §4.4 contra las que se mide RoBERTuito.

DOS BASELINES:
 1. AFINN extendido + reglas heurísticas: aplica afinn_scorer.py y mapea
    a una de las cuatro clases con reglas explícitas (es la línea base
    LÉXICA pura, la que la hipótesis predice que fallará en la ironía).
 2. pysentimiento ironía: clasificador preentrenado de detección de
    ironía en español. La hipótesis predice que será mejor que AFINN
    pero peor que el modelo fine-tuned (por falta de adaptación al
    dominio gamer específico).

Ambas líneas base se evalúan sobre el MISMO test set que el modelo
fine-tuned, con las mismas métricas, para comparabilidad directa.

Uso:
  python baselines.py --test splits/test.csv --baseline afinn --out baselines/
  python baselines.py --test splits/test.csv --baseline pysentimiento --out baselines/
  python baselines.py --test splits/test.csv --baseline all --out baselines/

DEPENDENCIAS:
  pip install pysentimiento  # solo para baseline pysentimiento
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# afinn_scorer.py vive en el mismo directorio (src/)
sys.path.insert(0, str(Path(__file__).parent))
try:
    from afinn_scorer import build_lexicon, score_text, IRONIC_RX, POSITIVE_WORDS_RX
except ImportError:
    print("AVISO: no se encuentra afinn_scorer.py en src/.", file=sys.stderr)
    print("Asegúrate de que afinn_scorer.py está junto a baselines.py.", file=sys.stderr)
    raise

LABELS = ["frustracion_explicita", "resignacion_ironica", "neutral", "otro"]


# --------------------------------------------------------------------------- #
# Baseline 1: AFINN extendido + reglas                                         #
# --------------------------------------------------------------------------- #

def predict_afinn(text: str, lexicon: dict) -> str:
    """Mapea (afinn_norm, marcadores) -> una de las 4 clases con reglas.

    Reglas (deliberadamente simples; representan lo que un enfoque
    léxico puede ofrecer sin contexto):
      - Si hay marcador irónico Y léxico positivo o neutro: ironía.
      - Si afinn_norm <= -2: frustración explícita.
      - Si -2 < afinn_norm <= -0.5 SIN marcador positivo: frustración leve
        (se mapea a frustración explícita).
      - Si |afinn_norm| < 0.5: neutral.
      - Si afinn_norm >= 0.5 sin marcador irónico: otro
        (positivo genuino en hilo de quejas: probablemente off-topic).
    """
    total, hits, norm = score_text(text, lexicon)
    ironic = bool(IRONIC_RX.search(text))
    has_pos = bool(POSITIVE_WORDS_RX.search(text))

    if ironic and (norm >= -1 or has_pos):
        return "resignacion_ironica"
    if norm <= -2:
        return "frustracion_explicita"
    if norm <= -0.5:
        return "frustracion_explicita"
    if abs(norm) < 0.5:
        return "neutral"
    # norm >= 0.5
    if ironic:
        return "resignacion_ironica"
    return "otro"


# --------------------------------------------------------------------------- #
# Baseline 2: pysentimiento ironía                                             #
# --------------------------------------------------------------------------- #

def predict_pysentimiento(rows: list[dict], text_col: str) -> list[str]:
    """Combina dos clasificadores de pysentimiento:
       - irony detector (ironic / not ironic);
       - sentiment analyzer (POS / NEG / NEU).
    Mapeo:
       - ironic            -> resignacion_ironica
       - not ironic + NEG  -> frustracion_explicita
       - not ironic + NEU  -> neutral
       - not ironic + POS  -> otro (positivo no irónico en hilo de quejas)
    """
    try:
        from pysentimiento import create_analyzer
    except ImportError:
        print("pysentimiento no está instalado. pip install pysentimiento",
              file=sys.stderr)
        raise

    irony = create_analyzer(task="irony", lang="es")
    sent = create_analyzer(task="sentiment", lang="es")

    texts = [r[text_col] for r in rows]
    irony_preds = [irony.predict(t).output for t in texts]
    sent_preds = [sent.predict(t).output for t in texts]

    out = []
    for ip, sp in zip(irony_preds, sent_preds):
        if ip == "ironic":
            out.append("resignacion_ironica")
        elif sp == "NEG":
            out.append("frustracion_explicita")
        elif sp == "NEU":
            out.append("neutral")
        else:  # POS
            out.append("otro")
    return out


# --------------------------------------------------------------------------- #
# Evaluación común                                                             #
# --------------------------------------------------------------------------- #

def evaluate(y_true: list[str], y_pred: list[str], name: str, out_dir: Path):
    from sklearn.metrics import (classification_report, confusion_matrix,
                                 f1_score, accuracy_score,
                                 precision_recall_fscore_support)
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", labels=LABELS, zero_division=0)
    per_class = f1_score(y_true, y_pred, average=None, labels=LABELS,
                         zero_division=0)
    report = classification_report(y_true, y_pred, labels=LABELS,
                                   digits=4, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=LABELS).tolist()

    print(f"\n== Baseline: {name} ==")
    print(report)
    print(f"Matriz de confusión (filas=verdadero, columnas=predicho):")
    print(f"    {'':25}" + "".join(f"{l[:10]:>12}" for l in LABELS))
    for i, l in enumerate(LABELS):
        print(f"    {l:<25}" + "".join(f"{cm[i][j]:>12}" for j in range(len(LABELS))))

    summary = {
        "name": name, "accuracy": acc, "macro_f1": f1,
        "macro_precision": prec, "macro_recall": rec,
        "per_class_f1": {l: float(s) for l, s in zip(LABELS, per_class)},
        "confusion_matrix": cm, "labels": LABELS,
    }
    with (out_dir / f"{name}_summary.json").open("w") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Baselines de §4.4.")
    ap.add_argument("--test", type=Path, required=True,
                    help="CSV de test con etiquetas (test.csv del Sprint 4).")
    ap.add_argument("--label-col", default="etiqueta_final")
    ap.add_argument("--text-col", default="content_raw")
    ap.add_argument("--baseline", choices=["afinn", "pysentimiento", "all"],
                    default="all")
    ap.add_argument("--inventory", type=Path,
                    default=Path(__file__).parent.parent / "data" / "inventory_emic_destilado.csv",
                    help="Inventario emic (para AFINN extendido).")
    ap.add_argument("--out", type=Path, default=Path("baselines"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(args.test, encoding="utf-8-sig")))
    y_true = [r[args.label_col].strip().lower() for r in rows]
    print(f"Test set: {len(rows)} mensajes")

    summaries = {}
    if args.baseline in ("afinn", "all"):
        lex = build_lexicon(args.inventory, None)
        print(f"Léxico AFINN: {len(lex)} entradas")
        y_pred = [predict_afinn(r[args.text_col], lex) for r in rows]
        summaries["afinn"] = evaluate(y_true, y_pred, "afinn", args.out)
        # Volcar predicciones
        with (args.out / "afinn_predictions.csv").open("w", encoding="utf-8-sig",
                                                       newline="") as fh:
            w = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
            w.writerow(["msg_id", "true", "pred", "text"])
            for r, t, p in zip(rows, y_true, y_pred):
                w.writerow([r.get("msg_id", ""), t, p, r[args.text_col]])

    if args.baseline in ("pysentimiento", "all"):
        y_pred = predict_pysentimiento(rows, args.text_col)
        summaries["pysentimiento"] = evaluate(y_true, y_pred, "pysentimiento",
                                              args.out)

    # Comparativa final
    if len(summaries) > 1:
        print("\n== COMPARATIVA ==")
        print(f"{'Baseline':<20} {'macro_f1':>10} {'f1_ironia':>12} {'acc':>8}")
        for name, s in summaries.items():
            print(f"{name:<20} {s['macro_f1']:>10.4f} "
                  f"{s['per_class_f1']['resignacion_ironica']:>12.4f} "
                  f"{s['accuracy']:>8.4f}")
        print("\n(Más adelante, comparar con RoBERTuito fine-tuned. La hipótesis")
        print(" predice ganancia notable, sobre todo en f1_resignacion_ironica.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
