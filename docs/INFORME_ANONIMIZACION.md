# Informe de anonimización del subcorpus anotado

Documento de trazabilidad del proceso de seudonimización aplicado a
`subcorpus_anotado_FINAL.csv` antes de su publicación. Forma parte de los
recursos del TFM (Máster DaSoc, USAL-UGR, 2025-2026). El subcorpus publicado en
el repositorio es la versión anonimizada; la tabla de equivalencia
(`mapa_seudonimos.csv`) **no se publica** y permanece bajo control del
investigador.

## 1. Material

- Entrada: `subcorpus_anotado_FINAL.csv` (1.200 mensajes anotados).
- Salida pública: `subcorpus_anotado_FINAL_anon.csv` (1.200 mensajes).
- Salida privada (no repositorio): `mapa_seudonimos.csv`.

El subcorpus no contiene campo de autor: el único vector de reidentificación es
el texto libre (`content_raw`). El resto de columnas (`orden`, `msg_id`, `año`,
`afinn_norm`, `ironic_marker`, las tres etiquetas y `notas`) no contienen datos
personales de terceros.

## 2. Vectores de reidentificación examinados

| Vector | Método de detección | Hallazgos |
|---|---|---|
| Menciones `@nick` | expresión regular | 0 |
| Citas «X escribió:» | expresión regular | 0 (el rascador extrajo el cuerpo del mensaje sin el encabezado de cita) |
| Identificadores de post citados `#NNNN` | expresión regular | 289, normalizados a `[cita]` |
| URLs | expresión regular | 20, todas a recursos públicos (Riot, Reddit, foros oficiales, Wikipedia, alojadores de imágenes); ninguna a perfil de usuario |
| Nombres de persona en texto (vocativos, `Riot X`, *CamelCase*) | reglas + revisión manual | 2 personas reales tras descartar falsos positivos |

## 3. Personas seudonimizadas

| Original | Marcador | Naturaleza |
|---|---|---|
| (forero) | `[usuario]` | usuario del foro identificado por otro en un vocativo |
| (empleado de Riot) | `[rioter]` | personal de Riot Games citado en respuesta oficial |

Se optó por marcadores genéricos (`[usuario]`, `[rioter]`) en lugar de
identificadores numerados porque solo hay un caso de cada tipo y el marcador
genérico elimina cualquier capacidad de seguimiento entre menciones.

## 4. Falsos positivos descartados

`Riot Client` y `Riot Points` (componentes y moneda del juego, no personas);
`DigiMobil` (operadora), `LeaverBuster`, `LeBlanc`, `IpV6` (términos del
ecosistema del juego y técnicos).

## 5. Resultado

277 de 1.200 filas modificadas (289 sustituciones de `[cita]` + 2 de persona).
Integridad verificada: número de filas, columnas, `msg_id` y distribución de
clases idénticos al original; sin residuos de los nombres originales en la
salida pública.

## 6. Límites declarados

La detección de nombres de persona en texto libre se realizó por reglas y
revisión manual, **no** por cotejo contra el censo de autores del corpus
completo (no disponible en esta fase). En consecuencia, no puede garantizarse la
detección de un nombre propio escrito en minúscula o de forma no convencional
que no haya activado ninguna regla ni la revisión. Dado el reducido número de
candidatos (4) y la limpieza del texto (sin menciones `@` ni encabezados de
cita), el riesgo residual se considera bajo, pero se documenta expresamente en
lugar de afirmar una anonimización exhaustiva. El texto coloquial puede contener
referencias contextuales indirectas no estructuradas, inherentes a cualquier
corpus de foro.
