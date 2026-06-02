#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
afinn_scorer.py — Puntuación de polaridad AFINN-extendido-con-inventario-emic.

Dos funciones en el TFM:
 1. LÍNEA BASE (§4.4): puntuación de polaridad léxica por mensaje sobre la
    totalidad del corpus, que sirve de referencia contra la que medir la
    ganancia de RoBERTuito en el conjunto de prueba. La agregación temporal
    de esta puntuación en una curva diacrónica de polaridad no se realiza
    aquí: queda reservada al plano confirmatorio (§4.8) y a las líneas
    futuras (§6.3).
 2. INSUMO DEL MUESTREO (§4.3): proporciona la puntuación por mensaje que
    permite sobrerrepresentar los mensajes con valencia próxima a cero
    (los más ambiguos para los métodos léxicos y los más relevantes para
    la hipótesis de la deflación afectiva).

LÉXICO. El scorer combina:
 - el inventario emic destilado (columna valencia_AFINN_extendida), que es
   el aporte específico del TFM; y
 - una semilla compacta de polaridad del español general (abajo).

HONESTIDAD METODOLÓGICA: la semilla del español general es modesta y NO
sustituye a un lexicón AFINN-es completo. Para la línea base definitiva de
§4.4 conviene fusionar un AFINN-es publicado (p. ej. adaptaciones de
Redondo et al. o el ML-SentiCon) mediante --extra-lexicon. Para el PROPÓSITO
DEL MUESTREO (detectar mensajes de valencia ~0) la combinación actual es
suficiente: lo que importa ahí es ordenar por intensidad, no la precisión
absoluta de cada valor.

Uso:
  # Puntuar un CSV de mensajes (añade columnas afinn_score, afinn_norm, flags)
  python afinn_scorer.py --in mensajes.csv --out mensajes_scored.csv

  # Con lexicón AFINN-es externo adicional (formato: palabra<TAB>valor por línea)
  python afinn_scorer.py --in mensajes.csv --out out.csv --extra-lexicon afinn_es.tsv

  # Sobre la BD directamente (volcando a CSV)
  python afinn_scorer.py --db corpus.db --out corpus_scored.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

# --------------------------------------------------------------------------- #
# Semilla de polaridad del español general (compacta, ampliable).            #
# Valores -5..+5 al estilo AFINN. NO exhaustiva: complementa al inventario.  #
# --------------------------------------------------------------------------- #
SEED_LEXICON = {
    # negativos fuertes
    "mierda": -4, "puto": -4, "puta": -4, "asco": -4, "odio": -4, "cabron": -4,
    "cabrones": -4, "hijoputa": -5, "hijosdeputa": -5, "joder": -3, "jodido": -3,
    "basura": -4, "horrible": -4, "inutil": -3, "inutiles": -3, "incompetente": -3,
    "incompetentes": -3, "verguenza": -3, "patetico": -3, "lamentable": -3,
    "insoportable": -4, "imposible": -2, "fail": -3, "muerete": -5, "suicidio": -4,
    "harto": -3, "cansado": -2, "ladrones": -4, "vomito": -4,
    # negativos medios/leves (técnicos cargados)
    "lag": -2, "lagazo": -3, "caido": -2, "petar": -2, "petado": -2, "petao": -2,
    "cola": -1, "ping": -1, "bug": -2, "error": -2, "troll": -2, "trolles": -2,
    "afk": -2, "dc": -2, "desconecta": -2, "desconexion": -2, "ban": -2,
    "lageado": -2, "laggeado": -2, "freeze": -2, "crash": -3, "down": -2,
    # positivos (clave: son los que la ironía invierte)
    "genial": 3, "perfecto": 3, "maravilla": 4, "encanta": 4, "bien": 2,
    "encantado": 3, "gracias": 2, "lujo": 2, "divertido": 3, "epico": 3,
    "epica": 3, "grande": 2, "bueno": 2, "buenisimo": 4, "alegro": 3,
    "feliz": 3, "yeah": 2, "aleluya": 2, "easy": 2, "fenomenos": 3,
}

# --------------------------------------------------------------------------- #
# Marcadores de ironía (de las categorías del inventario emic).              #
# Su presencia, sobre todo junto a léxico positivo, señala probable          #
# resignación irónica: oro para sobremuestrear la clase minoritaria.         #
# --------------------------------------------------------------------------- #
IRONIC_MARKERS = [
    r"\brito\b", r"indie compa", r"gg\s*rito", r"rito\s*pl", r"rito\s*gg",
    r"euw\s*strike", r"never fail", r"disfruten lo votado", r"seems legit",
    r"oh wait", r"\bnovedad", r"como siempre", r"vease ironia", r"era ironico",
    r"thereisno", r"konami", r"\brip\b", r"\bgg\b",
]
IRONIC_RX = re.compile("|".join(IRONIC_MARKERS), re.IGNORECASE)

# Léxico positivo para detectar "positivo en contexto de queja"
POSITIVE_WORDS_RX = re.compile(
    r"\b(genial|perfecto|maravilla|encanta|encantado|divertido|lujo|"
    r"gracias|yeah|epic[ao]|fenomenos|grande|de lujo|que bien|qué bien)\b",
    re.IGNORECASE,
)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def load_inventory_valences(inv_path: Path) -> dict[str, int]:
    """Extrae {token_normalizado: valencia} del inventario emic."""
    out: dict[str, int] = {}
    if not inv_path or not inv_path.exists():
        return out
    with inv_path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            base = (row.get("variante_normalizada") or row.get("termino") or "").strip()
            val = row.get("valencia_AFINN_extendida", "").strip()
            if not base or not val:
                continue
            try:
                v = int(float(val))
            except ValueError:
                continue
            core = re.sub(r"\(.*?\)", "", base).strip().strip("¿?¡!.:«»\"' ")
            core = strip_accents(core.lower())
            # solo tokens de 1-3 palabras, útiles para matching
            if core and len(core.split()) <= 3:
                out[core] = v
    return out


def load_extra_lexicon(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    if not path or not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"\t|,|;", line)
        if len(parts) < 2:
            continue
        word = strip_accents(parts[0].strip().lower())
        try:
            out[word] = int(float(parts[1]))
        except ValueError:
            continue
    return out


def build_lexicon(inv_path: Path | None, extra_path: Path | None) -> dict[str, int]:
    lex = dict(SEED_LEXICON)
    lex = {strip_accents(k): v for k, v in lex.items()}
    inv = load_inventory_valences(inv_path) if inv_path else {}
    extra = load_extra_lexicon(extra_path) if extra_path else {}
    # prioridad: inventario emic > extra > semilla (el emic es el aporte del TFM)
    lex.update(extra)
    lex.update(inv)
    return lex


TOKEN_RX = re.compile(r"[a-záéíóúñ]+", re.IGNORECASE)


def score_text(text: str, lexicon: dict[str, int]) -> tuple[int, int, float]:
    """Devuelve (suma_valencia, n_tokens_con_valencia, score_normalizado)."""
    if not text:
        return (0, 0, 0.0)
    norm = strip_accents(text.lower())
    # multi-palabra del léxico primero (p. ej. "como siempre", "de lujo")
    total = 0
    hits = 0
    consumed = norm
    for term, val in lexicon.items():
        if " " in term and term in consumed:
            n = consumed.count(term)
            total += val * n
            hits += n
            consumed = consumed.replace(term, " ")
    for tok in TOKEN_RX.findall(consumed):
        if tok in lexicon:
            total += lexicon[tok]
            hits += 1
    norm_score = total / hits if hits else 0.0
    return (total, hits, round(norm_score, 3))


def annotate_rows(rows: list[dict], lexicon: dict[str, int]) -> list[dict]:
    for r in rows:
        text = r.get("content_raw", "") or ""
        total, hits, norm = score_text(text, lexicon)
        ironic = bool(IRONIC_RX.search(text))
        has_pos = bool(POSITIVE_WORDS_RX.search(text))
        # "difícil para léxico": valencia ~0, o positivo CON marcador irónico
        hard = (abs(norm) <= 1.0) or (norm > 0 and ironic)
        # candidato a resignación irónica: positivo o neutro + marcador irónico
        iron_candidate = ironic and (norm >= -1 or has_pos)
        r["afinn_score"] = total
        r["afinn_hits"] = hits
        r["afinn_norm"] = norm
        r["ironic_marker"] = int(ironic)
        r["positive_word"] = int(has_pos)
        r["hard_for_lexicon"] = int(hard)
        r["irony_candidate"] = int(iron_candidate)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="AFINN extendido con inventario emic.")
    ap.add_argument("--in", dest="infile", type=Path, help="CSV de entrada con columna content_raw.")
    ap.add_argument("--db", type=Path, help="Alternativa: leer mensajes de corpus.db.")
    ap.add_argument("--out", type=Path, required=True, help="CSV de salida.")
    ap.add_argument("--inventory", type=Path, default=Path("inventory_emic_destilado.csv"))
    ap.add_argument("--extra-lexicon", type=Path, default=None,
                    help="Lexicón AFINN-es adicional (palabra<TAB>valor).")
    args = ap.parse_args()

    lexicon = build_lexicon(args.inventory, args.extra_lexicon)
    print(f"Léxico: {len(lexicon)} entradas "
          f"(semilla {len(SEED_LEXICON)} + inventario + extra)", file=sys.stderr)

    if args.db:
        conn = sqlite3.connect(args.db)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(
            "SELECT msg_id, timestamp, user_hash, content_raw FROM messages "
            "WHERE content_raw IS NOT NULL AND TRIM(content_raw) != ''")]
        conn.close()
        for r in rows:
            r["anio"] = (r.get("timestamp") or "")[:4]
    elif args.infile:
        rows = list(csv.DictReader(open(args.infile, encoding="utf-8-sig")))
    else:
        ap.error("Indica --in o --db")

    rows = annotate_rows(rows, lexicon)

    base_fields = ["msg_id", "anio", "fecha_iso", "timestamp", "user_hash", "content_raw"]
    score_fields = ["afinn_score", "afinn_hits", "afinn_norm", "ironic_marker",
                    "positive_word", "hard_for_lexicon", "irony_candidate"]
    present = [f for f in base_fields if rows and f in rows[0]]
    fields = present + score_fields

    with args.out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL,
                           lineterminator="\r\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # Resumen
    n = len(rows)
    hard = sum(r["hard_for_lexicon"] for r in rows)
    iro = sum(r["irony_candidate"] for r in rows)
    print(f"Puntuados {n} mensajes. hard_for_lexicon={hard} ({100*hard/n:.1f}%), "
          f"irony_candidate={iro} ({100*iro/n:.1f}%)", file=sys.stderr)
    print(f"Salida: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
