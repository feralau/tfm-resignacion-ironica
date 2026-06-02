# Datos

## Recursos publicados

- `subcorpus/subcorpus_anotado_FINAL_anon.csv` — subcorpus anotado anonimizado
  (1.200 mensajes; distribución 577/271/239/113). **Estado: final.**
- `splits/{train,val,test}.csv` — particiones anonimizadas (963/117/120, semilla
  2024, estratificadas por clase y fase, sin fuga de `msg_id`). **Estado: final.**
- `autores_corpus.csv` — tabla de los 4.419 autores del corpus completo, ya
  seudonimizada en origen (`usuario_NNNN` + `user_hash`; sin nicks en claro). La
  suma de `n_mensajes` es 50.512, consistente con el corpus completo.
  **Estado: final (recurso de trazabilidad).**
- `inventory_emic_destilado.csv` — inventario emic destilado, recurso léxico del
  baseline AFINN (`src/baselines.py --inventory`). **Estado: final.**

## Estado del inventario emic

El inventario contiene 42 entradas en 9 categorías pragmáticas. Su estado es
**final**: las columnas `categoria_pragmatica` y `valencia_AFINN_extendida`
han sido validadas término a término por el investigador. Se ha aplicado,
además, un control de calidad de las **referencias** al corpus:

- 41 de las 42 entradas tienen el `ejemplo_corpus_msg_id` verificado contra el
  corpus completo (todos los `msg_id` existen en el corpus de 50.512 mensajes;
  trazabilidad anotada en `notas`).
- 1 entrada (`:@@@@@ / emoticono iterado`) no tiene `msg_id`: su ejemplo es
  una ristra de emoticonos sin texto, no localizable por búsqueda textual.

## Anonimización

Todos los textos van anonimizados con el mismo procedimiento (`[usuario]`,
`[rioter]`, `[cita]`); ver `docs/INFORME_ANONIMIZACION.md`.
