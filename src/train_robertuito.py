#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_robertuito.py — Fine-tuning del clasificador RoBERTuito (§4.4).

Implementa el protocolo descrito en el TFM:
 - Modelo base: pysentimiento/robertuito-base-uncased (125M parámetros).
 - Arquitectura: encoder + cabeza lineal sobre [CLS] -> 4 clases.
 - Optimizador: AdamW con weight decay.
 - LR: malla Sun et al. (2019): {2e-5, 3e-5, 5e-5}.
 - Calentamiento lineal 10% de pasos totales -> decaimiento lineal.
 - Épocas: máx. 5 con parada temprana sobre val loss.
 - Batch: 16 o 32 según GPU disponible.
 - Longitud máx.: 128 tokens (percentil 95 del corpus).
 - Desbalanceo: class weights inversamente proporcional a la frecuencia,
   integrados en la CrossEntropyLoss (alternativa: --focal para focal loss).
 - Métricas: macro F1 (primaria), precision, recall, accuracy, F1 por clase
   (énfasis en F1 de resignacion_ironica).

Uso:
    python train_robertuito.py --data-dir splits/ --out-dir runs/run1/ \
        --lr 2e-5 --batch-size 16 --epochs 5 --seed 2024

    # Búsqueda en malla (lanza varios entrenamientos)
    python train_robertuito.py --data-dir splits/ --out-dir runs/grid/ \
        --grid-search

    # Validación cruzada k-fold (recomendada por la varianza con n=1200)
    python train_robertuito.py --data-dir splits/ --kfold 5 --lr 3e-5

DEPENDENCIAS:
    pip install torch transformers datasets scikit-learn pandas numpy

CÓMPUTO esperado:
    Una configuración (5 épocas, 1.000 train, batch 16, max_len 128):
    ~5-10 min en GPU consumer (RTX 3060+); ~30-45 min en T4 de Colab Free.
    Malla completa de 3 LR: x3. K-fold k=5: x5. La malla + 5-fold = 15
    runs, ~2-3 h en GPU media. Planifica en función de tu cómputo.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd

# Imports pesados se hacen dentro de main() para que --help sea rápido
# y para que el script se pueda inspeccionar sin tener torch instalado.

LABEL2ID = {
    "frustracion_explicita": 0,
    "resignacion_ironica": 1,
    "neutral": 2,
    "otro": 3,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
MODEL_NAME = "pysentimiento/robertuito-base-uncased"


def set_seed(seed: int) -> None:
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_split(path: Path, label_col: str, text_col: str):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.dropna(subset=[label_col, text_col])
    df[label_col] = df[label_col].str.strip().str.lower()
    df = df[df[label_col].isin(LABEL2ID)]
    df["label"] = df[label_col].map(LABEL2ID).astype(int)
    return df


def compute_class_weights(df, num_labels: int):
    import torch
    counts = df["label"].value_counts().sort_index()
    counts = counts.reindex(range(num_labels), fill_value=0)
    total = counts.sum()
    # Inversamente proporcional a la frecuencia; normalizado para que la media sea 1
    weights = (total / (num_labels * counts.clip(lower=1))).astype(float)
    weights = weights / weights.mean()
    return torch.tensor(weights.values, dtype=torch.float)


def build_tokenize_fn(tokenizer, text_col: str, max_len: int):
    def fn(batch):
        return tokenizer(batch[text_col], truncation=True, max_length=max_len,
                         padding=False)
    return fn


def compute_metrics_fn():
    from sklearn.metrics import (accuracy_score, precision_recall_fscore_support,
                                 f1_score, classification_report)

    def fn(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        acc = accuracy_score(labels, preds)
        prec, rec, f1, _ = precision_recall_fscore_support(
            labels, preds, average="macro", zero_division=0)
        per_class_f1 = f1_score(labels, preds, average=None,
                                labels=list(range(len(LABEL2ID))),
                                zero_division=0)
        out = {"accuracy": acc, "macro_f1": f1, "macro_precision": prec,
               "macro_recall": rec}
        for cls_id, score in enumerate(per_class_f1):
            out[f"f1_{ID2LABEL[cls_id]}"] = float(score)
        return out
    return fn


def train_single(args, lr, fold_id: str = "single"):
    """Entrena una configuración (un LR, un split o un fold). Devuelve metrics."""
    import torch
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                              Trainer, TrainingArguments, DataCollatorWithPadding,
                              EarlyStoppingCallback)
    from datasets import Dataset

    set_seed(args.seed)

    out_dir = args.out_dir / fold_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Datos
    train_df = load_split(args.data_dir / "train.csv", args.label_col, args.text_col)
    val_df = load_split(args.data_dir / "val.csv", args.label_col, args.text_col)
    test_df = load_split(args.data_dir / "test.csv", args.label_col, args.text_col)

    print(f"\n[{fold_id}] train={len(train_df)} val={len(val_df)} test={len(test_df)}")
    print(f"[{fold_id}] LR={lr} batch={args.batch_size} epochs={args.epochs}")

    # Preprocesador de dominio (opcional)
    if args.use_preprocessor:
        from gamer_preprocessor import GamerPreprocessor
        pre = GamerPreprocessor()
        train_df[args.text_col] = train_df[args.text_col].apply(pre.transform)
        val_df[args.text_col] = val_df[args.text_col].apply(pre.transform)
        test_df[args.text_col] = test_df[args.text_col].apply(pre.transform)

    # Tokenizador
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tok_fn = build_tokenize_fn(tokenizer, args.text_col, args.max_len)

    train_ds = Dataset.from_pandas(train_df[[args.text_col, "label"]]).map(
        tok_fn, batched=True, remove_columns=[args.text_col])
    val_ds = Dataset.from_pandas(val_df[[args.text_col, "label"]]).map(
        tok_fn, batched=True, remove_columns=[args.text_col])
    test_ds = Dataset.from_pandas(test_df[[args.text_col, "label"]]).map(
        tok_fn, batched=True, remove_columns=[args.text_col])

    # Modelo
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    # Class weights
    class_weights = compute_class_weights(train_df, len(LABEL2ID))
    print(f"[{fold_id}] class_weights = {class_weights.tolist()}")

    # Trainer con loss customizado
    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits
            if args.focal:
                # Focal loss (alternativa a class weights)
                ce = torch.nn.functional.cross_entropy(logits, labels, reduction="none")
                pt = torch.exp(-ce)
                loss = ((1 - pt) ** args.focal_gamma * ce).mean()
            else:
                loss_fn = torch.nn.CrossEntropyLoss(
                    weight=class_weights.to(logits.device))
                loss = loss_fn(logits, labels)
            return (loss, outputs) if return_outputs else loss

    # Calentamiento lineal 10% (Sun et al. 2019)
    total_steps = (len(train_ds) // args.batch_size) * args.epochs
    warmup_steps = max(1, int(0.1 * total_steps))

    # `eval_strategy` (transformers nuevo) vs `evaluation_strategy` (antiguo).
    import inspect as _inspect
    _ta_params = _inspect.signature(TrainingArguments.__init__).parameters
    _eval_kw = "eval_strategy" if "eval_strategy" in _ta_params else "evaluation_strategy"

    training_args = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        learning_rate=lr,
        weight_decay=0.01,
        warmup_steps=warmup_steps,
        lr_scheduler_type="linear",
        save_strategy="epoch",
        load_best_model_at_end=True,
        # En transformers v4 y v5, el callback/Trainer añaden el prefijo "eval_"
        # automáticamente a esta métrica. Se nombra SIN prefijo (forma canónica).
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        save_total_limit=1,
        logging_steps=50,
        report_to=[],  # sin wandb/tensorboard por defecto
        seed=args.seed,
        fp16=torch.cuda.is_available() and not args.no_fp16,
        **{_eval_kw: "epoch"},
    )

    # En transformers >=4.46 el argumento `tokenizer` del Trainer se renombró
    # a `processing_class`. Detectamos cuál acepta esta versión para que el
    # script funcione en ambos casos (entorno Colab actual y entornos antiguos).
    import inspect
    _trainer_params = inspect.signature(Trainer.__init__).parameters
    _tok_kw = "processing_class" if "processing_class" in _trainer_params else "tokenizer"

    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics_fn(),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
        **{_tok_kw: tokenizer},
    )

    print(f"[{fold_id}] entrenando...")
    trainer.train()

    # El EarlyStoppingCallback solo tiene sentido durante el bucle de
    # entrenamiento (métricas con prefijo eval_). En las evaluaciones manuales
    # de abajo, las claves llevan prefijo test_, y el callback emitiría un
    # warning inocuo ("did not find eval_macro_f1"). Lo retiramos para que el
    # log quede limpio; no afecta al modelo ya entrenado ni a las métricas.
    trainer.remove_callback(EarlyStoppingCallback)

    # Métricas val + test
    val_metrics = trainer.evaluate(val_ds)
    test_metrics = trainer.evaluate(test_ds, metric_key_prefix="test")

    # Predicciones detalladas en test para análisis de errores
    preds_test = trainer.predict(test_ds)
    test_df_out = test_df.copy()
    test_df_out["predicted_id"] = np.argmax(preds_test.predictions, axis=-1)
    test_df_out["predicted_label"] = test_df_out["predicted_id"].map(ID2LABEL)
    test_df_out["correct"] = test_df_out["predicted_id"] == test_df_out["label"]
    test_df_out.to_csv(out_dir / "test_predictions.csv", index=False,
                       encoding="utf-8-sig")

    # Resumen
    summary = {
        "fold": fold_id, "lr": lr, "batch_size": args.batch_size,
        "epochs": args.epochs, "seed": args.seed, "use_preprocessor": args.use_preprocessor,
        "focal_loss": args.focal,
        "val_metrics": {k: v for k, v in val_metrics.items() if not k.startswith("_")},
        "test_metrics": {k: v for k, v in test_metrics.items() if not k.startswith("_")},
        "class_weights": class_weights.tolist(),
    }
    with (out_dir / "summary.json").open("w") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    print(f"[{fold_id}] DONE. macro_f1 test = {test_metrics.get('test_macro_f1', 0):.4f}")
    print(f"[{fold_id}] f1 resignacion_ironica = "
          f"{test_metrics.get('test_f1_resignacion_ironica', 0):.4f}")

    # Guardar el mejor modelo
    trainer.save_model(str(out_dir / "best_model"))

    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Fine-tuning RoBERTuito (Sprint 4).")
    ap.add_argument("--data-dir", type=Path, default=Path("splits"),
                    help="Directorio con train.csv, val.csv, test.csv")
    ap.add_argument("--out-dir", type=Path, default=Path("runs/run1"))
    ap.add_argument("--label-col", default="etiqueta_final")
    ap.add_argument("--text-col", default="content_raw")
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--seed", type=int, default=2024)
    ap.add_argument("--use-preprocessor", action="store_true",
                    help="Aplicar gamer_preprocessor antes de tokenizar.")
    ap.add_argument("--focal", action="store_true",
                    help="Usar focal loss en lugar de class weights.")
    ap.add_argument("--focal-gamma", type=float, default=2.0)
    ap.add_argument("--no-fp16", action="store_true",
                    help="Desactivar fp16 (útil en CPU o GPUs antiguas).")
    ap.add_argument("--grid-search", action="store_true",
                    help="Lanza la malla {2e-5, 3e-5, 5e-5}.")
    ap.add_argument("--kfold", type=int, default=0,
                    help="k-fold cross validation con k folds (k>=2).")
    args = ap.parse_args()

    if args.kfold and args.kfold >= 2:
        return run_kfold(args)
    if args.grid_search:
        return run_grid(args)
    train_single(args, args.lr, "single")
    return 0


def run_grid(args) -> int:
    summaries = []
    for lr in [2e-5, 3e-5, 5e-5]:
        summaries.append(train_single(args, lr, f"lr{lr}"))
    with (args.out_dir / "grid_summary.json").open("w") as fh:
        json.dump(summaries, fh, indent=2, ensure_ascii=False)
    print("\n== Resumen grid ==")
    for s in summaries:
        print(f"  LR={s['lr']:.0e}  test_macro_f1="
              f"{s['test_metrics'].get('test_macro_f1', 0):.4f}  "
              f"f1_ironia={s['test_metrics'].get('test_f1_resignacion_ironica', 0):.4f}")
    return 0


def run_kfold(args) -> int:
    """Validación cruzada estratificada k-fold sobre train+val combinados.
    El test set se mantiene como hold-out final.
    """
    from sklearn.model_selection import StratifiedKFold
    import pandas as pd

    train_df = load_split(args.data_dir / "train.csv", args.label_col, args.text_col)
    val_df = load_split(args.data_dir / "val.csv", args.label_col, args.text_col)
    full = pd.concat([train_df, val_df], ignore_index=True)
    print(f"K-fold sobre {len(full)} ejemplos (train+val combinados), k={args.kfold}")
    skf = StratifiedKFold(n_splits=args.kfold, shuffle=True, random_state=args.seed)
    summaries = []
    for fold_id, (tr_idx, va_idx) in enumerate(skf.split(full, full["label"])):
        fold_dir = args.out_dir / f"fold{fold_id}"
        fold_dir.mkdir(parents=True, exist_ok=True)
        full.iloc[tr_idx].to_csv(fold_dir / "train.csv", index=False,
                                 encoding="utf-8-sig")
        full.iloc[va_idx].to_csv(fold_dir / "val.csv", index=False,
                                 encoding="utf-8-sig")
        # test se reutiliza
        (args.data_dir / "test.csv").read_text(encoding="utf-8-sig")
        import shutil
        shutil.copy(args.data_dir / "test.csv", fold_dir / "test.csv")
        # Re-apuntar data_dir temporalmente
        saved = args.data_dir
        args.data_dir = fold_dir
        try:
            summaries.append(train_single(args, args.lr, f"fold{fold_id}"))
        finally:
            args.data_dir = saved
    # Estadísticas agregadas
    macros = [s["test_metrics"].get("test_macro_f1", 0) for s in summaries]
    ironia = [s["test_metrics"].get("test_f1_resignacion_ironica", 0) for s in summaries]
    agg = {
        "k": args.kfold,
        "lr": args.lr,
        "macro_f1_mean": float(np.mean(macros)),
        "macro_f1_std": float(np.std(macros)),
        "f1_ironia_mean": float(np.mean(ironia)),
        "f1_ironia_std": float(np.std(ironia)),
        "per_fold": summaries,
    }
    with (args.out_dir / "kfold_summary.json").open("w") as fh:
        json.dump(agg, fh, indent=2, ensure_ascii=False)
    print(f"\n== K-fold k={args.kfold} ==")
    print(f"  macro_f1 = {agg['macro_f1_mean']:.4f} ± {agg['macro_f1_std']:.4f}")
    print(f"  f1_ironia = {agg['f1_ironia_mean']:.4f} ± {agg['f1_ironia_std']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
