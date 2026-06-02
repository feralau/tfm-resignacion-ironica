# Código

Todos los scripts viven en este directorio (estructura aplanada: los imports
entre scripts funcionan sin rutas relativas entre carpetas).

- `gamer_preprocessor.py` — preprocesador de dominio. Es una **clase**
  (`GamerPreprocessor`), no un script de línea de comandos: se importa y se
  llama `.transform(texto)`. Ejecutarlo directamente (`python gamer_preprocessor.py`)
  corre su batería de auto-tests. Su uso en el entrenamiento es **opcional**,
  mediante la bandera `--use-preprocessor` de `train_robertuito.py`.
- `train_robertuito.py` — fine-tuning de RoBERTuito. Lee
  `--data-dir/{train,val,test}.csv`. Modos: entrenamiento simple,
  `--grid-search` (malla de LR, escribe `grid_summary.json` y guarda
  `best_model/`) y `--kfold N` (validación cruzada). Detecta la versión de
  `transformers`; `metric_for_best_model="macro_f1"`. Registra
  `use_preprocessor` en el JSON de salida para trazabilidad.
- `afinn_scorer.py` — léxico AFINN extendido con el inventario emic. **Requerido
  por `baselines.py`** (importa `build_lexicon`, `score_text`, `IRONIC_RX`,
  `POSITIVE_WORDS_RX`).
- `baselines.py` — líneas base AFINN y pysentimiento sobre el test.

## Reproducción

Ver `reproduce.sh` en la raíz. Importante: la variable `PREPROCESSOR` de ese
script debe coincidir con el campo `use_preprocessor` registrado en
`results/grid/grid_summary.json`, para reproducir exactamente el modelo final.

## Líneas base

```bash
python src/baselines.py --test data/splits/test.csv \
    --inventory data/inventory_emic_destilado.csv \
    --baseline all --out results/baselines
```

El baseline AFINN recalcula la puntuación a partir del texto (`content_raw`)
con `afinn_scorer.py` y el inventario emic; no usa la columna `afinn_norm`
precalculada. Genera `afinn_summary.json`, `pysentimiento_summary.json` y
`afinn_predictions.csv`.
