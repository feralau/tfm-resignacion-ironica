# Métricas y análisis

## Incluidos en el repositorio

- `grid/grid_summary.json` — búsqueda en cuadrícula de LR (macro F1 en test).
  Es la fuente de la selección del modelo y de los pesos publicados, por lo que
  se versiona (no es regenerable sin relanzar toda la malla).
- `analysis/errores_por_confusion.md` — análisis de los 23 errores del test.
- `analysis/errores_summary.json` — resumen cuantitativo de los errores.
- `analysis/diachronic_exploratory.json` — proporciones de clase por año y por
  fase histórica sobre el subcorpus anotado (reproduce las cifras del TFM §4.8).
  Generado por `src/diachronic_exploratory.py`. Indicios exploratorios sobre la
  muestra anotada, no estimaciones poblacionales del hilo completo.

## Generados al ejecutar `reproduce.sh` (no versionados)

Las salidas siguientes no se incluyen en el repositorio de forma deliberada: se
regeneran de forma determinista (semilla 2024) a partir de los datos y el código
ya publicados, y sus cifras están documentadas en `model/MODEL_CARD.md` (§5) y
en el TFM, que son la fuente de referencia para el lector.

- `kfold/kfold_3e5_summary.json`, `kfold/kfold_5e5_summary.json` — validación
  cruzada de 5 pliegues (test como retención común).
- `baselines/*.json` — líneas base AFINN y pysentimiento sobre el mismo test.
