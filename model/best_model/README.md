# Mejor modelo (LR 5e-5)

Punto de control seleccionado en la búsqueda en malla (LR 5e-5, lote 16,
5 épocas, semilla 2024, `use_preprocessor=true`). Métricas en
`../MODEL_CARD.md` §5 y en `../../results/grid/grid_summary.json`.

## Archivos

- `config.json` — RobertaForSequenceClassification, 4 clases
  (id2label: 0=frustracion_explicita, 1=resignacion_ironica, 2=neutral, 3=otro),
  RoBERTuito base (768/12/12, vocab 30000), transformers 5.0.0.
- `model.safetensors` — pesos (~416 MB, float32, 201 tensores). **Git LFS.**
- `tokenizer.json` — tokenizador BPE autocontenido (vocab 30000 + merges).
- `tokenizer_config.json` — configuración del tokenizador (max_length 128).
- `training_args.bin` — argumentos de entrenamiento (trazabilidad).

## Carga

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
model = AutoModelForSequenceClassification.from_pretrained("model/best_model")
tok = AutoTokenizer.from_pretrained("model/best_model")
```

## Git LFS

`model.safetensors` se versiona mediante Git LFS (ver `.gitattributes` en la
raíz). Inicializa LFS **antes** del primer `git add`:

```bash
git lfs install
git lfs track "*.safetensors"
git add .gitattributes
```
