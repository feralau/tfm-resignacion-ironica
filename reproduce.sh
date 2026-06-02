#!/usr/bin/env bash
# Reproducción end-to-end del Sprint 4: del subcorpus anonimizado a las métricas.
# Uso: bash reproduce.sh
#
# Requisitos previos:
#   - data/splits/{train,val,test}.csv  (incluidos en el repo, anonimizados)
#   - data/inventory_emic_destilado.csv (para el baseline AFINN)
#   - pip install -r requirements.txt
set -euo pipefail

SEED=2024

# ¿El modelo final se entrenó con el preprocesador gamer? Confirmado en
# results/grid/grid_summary.json: use_preprocessor = true en todos los runs.
PREPROCESSOR="--use-preprocessor"

echo "[1/3] Búsqueda en malla de LR + selección del mejor modelo (5e-5)"
# --grid-search entrena la malla, escribe grid_summary.json y guarda best_model/
python src/train_robertuito.py \
    --data-dir data/splits --out-dir results/grid \
    --grid-search --seed "${SEED}" ${PREPROCESSOR}

echo "[2/3] Validación cruzada de 5 pliegues (3e-5 y 5e-5)"
python src/train_robertuito.py --data-dir data/splits \
    --kfold 5 --lr 3e-5 --out-dir results/kfold --seed "${SEED}" ${PREPROCESSOR}
python src/train_robertuito.py --data-dir data/splits \
    --kfold 5 --lr 5e-5 --out-dir results/kfold --seed "${SEED}" ${PREPROCESSOR}

echo "[3/3] Líneas base (AFINN + pysentimiento) sobre el mismo test"
python src/baselines.py --test data/splits/test.csv \
    --inventory data/inventory_emic_destilado.csv \
    --baseline all --out results/baselines

echo
echo "Hecho. Métricas en results/. Comparar con model/MODEL_CARD.md §5."
echo "NOTA: el mejor modelo queda en results/grid/.../best_model/; cópialo a"
echo "      model/best_model/ para publicarlo vía Git LFS."
