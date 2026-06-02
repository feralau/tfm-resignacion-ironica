# Clasificador de sentimiento en lenguaje gamer hispanohablante

Recursos abiertos del Trabajo de Fin de Máster en Ciencia de Datos aplicada a
las Ciencias Sociales (DaSoc), Universidad de Salamanca y Universidad de
Granada, curso 2025-2026.

El proyecto entrena un clasificador de análisis de sentimiento de cuatro clases
mediante *fine-tuning* de RoBERTuito sobre un hilo de la comunidad
hispanohablante de *League of Legends* en el foro Mediavida. La hipótesis de
investigación es que la comunidad ha transitado de la frustración explícita
directa hacia una **resignación irónica** —deflación afectiva: léxico neutro o
positivo para contenido negativo— como mecanismo de cohesión subcultural.

## Clases

| Clase | Definición operativa |
|---|---|
| `frustracion_explicita` | Carga emocional negativa directa, sin distancia irónica. |
| `resignacion_ironica` | Deflación afectiva: léxico neutro o positivo para contenido negativo; tono cínico o metarreflexivo. |
| `neutral` | Función fática o informativa pura. |
| `otro` | Humor absurdista u *off-topic* no clasificable en las anteriores. |

## Resultado principal

El F1 de la clase de interés teórico (`resignacion_ironica`) se sitúa en
**0,79-0,82** en validación cruzada de cinco pliegues, robusto entre pliegues.
La deflación afectiva es, por tanto, un fenómeno lingüísticamente detectable de
forma fiable. Las cifras completas, por clase y con su nota metodológica, están
en `model/MODEL_CARD.md`.

## Estructura del repositorio

```
.
├── README.md
├── LICENSE                  Código: MIT
├── LICENSE-DATA.md          Datos y modelo: CC BY 4.0
├── requirements.txt         Dependencias (torch sin fijar, ver nota)
├── reproduce.sh             Reproducción end-to-end
├── .gitattributes           Configuración de Git LFS
├── .gitignore               Excluye el mapa de seudónimos y datos crudos
├── data/
│   ├── subcorpus/           Subcorpus anotado anonimizado (1.200 mensajes)
│   └── splits/              Particiones train/val/test (semilla 2024)
├── src/                     Preprocesador, entrenamiento y líneas base
├── model/
│   ├── MODEL_CARD.md        Ficha del modelo (Mitchell et al., 2019)
│   └── best_model/          Mejor punto de control (LR 5e-5), pesos vía Git LFS
├── results/                 Métricas (malla, validación cruzada, baselines, errores)
└── docs/
    └── INFORME_ANONIMIZACION.md
```

## Datos

El subcorpus publicado (`data/subcorpus/subcorpus_anotado_FINAL_anon.csv`,
1.200 mensajes) está **anonimizado**: los nombres de persona del texto se
sustituyen por marcadores genéricos (`[usuario]`, `[rioter]`) y los
identificadores de mensajes citados por `[cita]`. El procedimiento y sus
límites se documentan en `docs/INFORME_ANONIMIZACION.md`. La tabla de
equivalencia **no** forma parte del repositorio.

Distribución de clases del subcorpus: neutral 577 (48,1 %),
`resignacion_ironica` 271 (22,6 %), `frustracion_explicita` 239 (19,9 %),
`otro` 113 (9,4 %).

## Reproducción

```bash
git clone <URL-del-repo>
cd <repo>
git lfs install        # los pesos del modelo viajan por Git LFS
pip install -r requirements.txt
bash reproduce.sh      # del subcorpus anonimizado a las métricas
```

**Nota sobre `torch`:** `requirements.txt` no fija la versión de `torch` de
forma deliberada. Fijarla rompe `torchvision` en Google Colab (error
`torchvision::nms does not exist`); se utiliza el `torch` del entorno. Todas las
ejecuciones usan semilla 2024.

**Nota sobre Git LFS:** el archivo de pesos (`model/best_model/model.safetensors`)
se almacena mediante Git LFS. Es necesario tener Git LFS instalado antes de
clonar para descargar los pesos; sin él, se obtendrá un puntero en lugar del
binario.

## Modelo base

`pysentimiento/robertuito-base-uncased` (RoBERTuito; Pérez et al., 2022),
preentrenado para texto de redes sociales en español.

## Usos no permitidos

El uso del modelo está sujeto a las restricciones de la ficha del modelo
(`model/MODEL_CARD.md`, §3). En particular, **no debe** emplearse para detección
de ideación suicida o cribado de salud mental, moderación automática sin
supervisión humana, vigilancia o perfilado de usuarios, ni generación de texto.

## Licencias

Este repositorio usa licenciamiento dual según el tipo de artefacto:

- **Código** (`src/`, `reproduce.sh`): MIT — `SPDX-License-Identifier: MIT` (`LICENSE`).
- **Datos y modelo** (`data/`, `model/best_model/`): CC BY 4.0 —
  `SPDX-License-Identifier: CC-BY-4.0` (`LICENSE-DATA.md`).

GitHub detecta automáticamente la licencia MIT del código a partir del archivo
`LICENSE`; la licencia de datos y modelo se declara en `LICENSE-DATA.md`.

## Cómo citar

> Alonso Aucejo, F. (2026). *Resignación irónica en el espacio liminal:
> evolución sociolingüística de una comunidad gamer hispanohablante. Un análisis
> diacrónico del hilo «os va el lol» en Mediavida (2010-actualidad)*. Trabajo de
> Fin de Máster, Máster
> Universitario en Ciencia de Datos aplicada a las Ciencias Sociales (DaSoc),
> Universidad de Salamanca y Universidad de Granada.
