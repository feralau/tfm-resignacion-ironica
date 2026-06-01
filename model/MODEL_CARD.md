# Model Card — Clasificador de sentimiento en lenguaje gamer hispanohablante

Ficha del modelo siguiendo el marco de Mitchell et al. (2019). Documenta los
datos de entrenamiento, el rendimiento por clase, los sesgos conocidos y los
usos no permitidos del modelo. Forma parte de los recursos abiertos del Trabajo
de Fin de Máster en Ciencia de Datos aplicada a las Ciencias Sociales (DaSoc),
USAL-UGR, curso 2025-2026.

---

## 1. Detalles del modelo

- **Desarrollador:** Fernando Alonso Aucejo (TFM, Máster DaSoc, USAL-UGR).
- **Año:** 2026.
- **Tipo de modelo:** clasificador de análisis de sentimiento de cuatro clases,
  obtenido por *fine-tuning* de un modelo de lenguaje tipo Transformer.
- **Modelo base:** `pysentimiento/robertuito-base-uncased` (RoBERTuito; Pérez
  et al., 2022), modelo preentrenado para texto de redes sociales en español.
- **Arquitectura:** encoder Transformer (125M parámetros) + cabeza de
  clasificación lineal sobre el token [CLS], proyectando sobre cuatro clases.
- **Lengua:** español (registro coloquial gamer hispanohablante).
- **Licencia:** CC BY 4.0.
- **Repositorio:** GitHub (código bajo licencia MIT; modelo y datos bajo CC BY 4.0).
- **Contacto:** a través del repositorio del proyecto.

### Clases de salida

| Clase | Definición operativa |
|---|---|
| `frustracion_explicita` | Carga emocional negativa directa, sin distancia irónica. |
| `resignacion_ironica` | Deflación afectiva: léxico neutro o positivo para contenido negativo; tono cínico o metarreflexivo. |
| `neutral` | Función fática o informativa pura. |
| `otro` | Humor absurdista u *off-topic* no clasificable en las anteriores. |

---

## 2. Usos previstos

- **Uso principal previsto:** análisis **agregado** del sentimiento en
  comunidades gamer hispanohablantes, en contextos de **investigación**
  académica (sociolingüística computacional, estudios de comunidades digitales).
- **Usuarios previstos:** investigadores e investigadoras que estudien
  comunidades digitales en español y dispongan de conocimiento del campo para
  interpretar los resultados.
- **Alcance:** el modelo clasifica el sentimiento **del mensaje**, sobre texto
  breve de foro en español coloquial con argot del ecosistema *League of Legends*.

---

## 3. Usos fuera de alcance y NO permitidos

Esta sección es de cumplimiento obligatorio. El modelo **no debe** emplearse
para los fines siguientes:

- **Detección de ideación suicida o cribado de salud mental.** El corpus de
  entrenamiento contiene fraseología de violencia hiperbólica idiomática
  (p. ej. expresiones de hartazgo melodramático ante un fallo técnico) que se
  anotó como frustración explícita, **no** como ideación real. El modelo no
  diagnostica ni detecta riesgo y no debe usarse con ese propósito bajo ninguna
  circunstancia.
- **Moderación automática sin supervisión humana.** No debe emplearse para
  tomar decisiones automáticas de moderación, sanción o bloqueo sin revisión
  por una persona.
- **Vigilancia, perfilado o identificación de usuarios individuales.** El
  modelo está concebido para análisis agregado, nunca para la caracterización
  o el seguimiento de personas concretas.
- **Generación de texto.** El modelo es un clasificador; además, dado el léxico
  ofensivo presente en el corpus (véase §6), no debe utilizarse como base para
  generar contenido.
- **Análisis dirigido por destinatario (*target-dependent*).** El modelo
  clasifica el sentimiento del mensaje en su conjunto; no identifica a quién se
  dirige una carga afectiva (p. ej. no distingue si un insulto apunta a la
  empresa o a otro usuario). No debe usarse para inferir el destinatario de una
  emoción u ofensa.

---

## 4. Datos de entrenamiento

- **Fuente:** hilo «os va el lol» del foro Mediavida (identificador 393501),
  comunidad hispanohablante de *League of Legends*. Corpus completo de 50.512
  mensajes (2010-2026), de distribución temporal bimodal (≈80 % en 2011-2014).
- **Subcorpus anotado:** 1.200 mensajes muestreados del corpus.
- **Procedimiento de anotación:** anotación manual por un único investigador en
  dos rondas independientes espaciadas en el tiempo (test-retest), sin asistencia
  de IA. Fiabilidad intra-anotador medida con kappa de Cohen = 0,9366
  (P observado = 0,9575; P esperado = 0,3297), interpretable como
  acuerdo casi perfecto (Landis y Koch, 1977).
- **Distribución de clases (subcorpus):** neutral 577 (48,1 %),
  `resignacion_ironica` 271 (22,6 %), `frustracion_explicita` 239 (19,9 %),
  `otro` 113 (9,4 %).
- **Particiones:** entrenamiento 963 / validación 117 / prueba 120, con
  estratificación por clase y por fase temporal (semilla 2024).
- **Preprocesado:** preprocesador de dominio propio (normalización de variantes
  ortográficas del argot, conservación de marcadores irónicos, marca de
  mayúscula sostenida, limpieza de artefactos de exportación).
- **Anonimización:** el subcorpus se publica exclusivamente en versión
  anonimizada. El subcorpus no contiene campo de autor, por lo que el único
  vector de reidentificación es el texto; los nombres de persona detectados en
  él se sustituyen por marcadores genéricos (`[usuario]` para foreros,
  `[rioter]` para personal de Riot citado) y los identificadores de mensajes
  citados se normalizan a `[cita]`. La tabla de equivalencia no se publica y
  permanece bajo control del investigador. El procedimiento y sus límites se
  documentan en el informe de anonimización del repositorio.

---

## 5. Rendimiento

Configuración seleccionada: tasa de aprendizaje 5e-5, lote 16, 5 épocas con
parada temprana por pérdida de validación; la tasa de aprendizaje se eligió por
macro F1 sobre el conjunto de prueba en la búsqueda en cuadrícula; ponderación
de clases inversa a la frecuencia; longitud máxima 128 tokens.

### Evaluación sobre el conjunto de prueba (n = 120)

| Métrica | Valor |
|---|---|
| Exactitud (*accuracy*) | 0,808 |
| Macro F1 | 0,772 |
| F1 `resignacion_ironica` | 0,821 |

### Métricas por clase (conjunto de prueba, modelo 5e-5)

| Clase | Precisión | Exhaustividad | F1 | Soporte |
|---|---|---|---|---|
| `frustracion_explicita` | 0,833 | 0,625 | 0,714 | 24 |
| `resignacion_ironica` | 0,821 | 0,821 | 0,821 | 28 |
| `neutral` | 0,825 | 0,881 | 0,852 | 59 |
| `otro` | 0,636 | 0,778 | 0,700 | 9 |
| **Promedio macro** | **0,779** | **0,776** | **0,772** | 120 |
| Promedio ponderado | 0,812 | 0,808 | 0,806 | 120 |

La clase de interés teórico, `resignacion_ironica`, presenta precisión y
exhaustividad equilibradas (0,821 ambas): el modelo no la sobre- ni
infrapredice. La menor exhaustividad corresponde a `frustracion_explicita`
(0,625), coherente con el análisis de errores: parte de los mensajes de
frustración expresados como reporte técnico sereno se clasifican como neutrales.
La clase minoritaria `otro` (soporte 9) es la de menor precisión, como cabe
esperar por su escaso tamaño y heterogeneidad.

### Validación cruzada de 5 pliegues (entrenamiento+validación = 1.080; prueba como retención común)

| Métrica | Media ± desviación típica |
|---|---|
| Macro F1 | 0,739 ± 0,023 |
| F1 `resignacion_ironica` | 0,794 ± 0,023 |

*Nota metodológica:* la desviación típica refleja la dispersión inducida por la
partición de entrenamiento entre pliegues; no constituye un intervalo de
confianza sobre el conjunto de prueba, que se mantiene como retención común.

### Comparación con líneas base (mismo conjunto de prueba)

| Modelo | Macro F1 | F1 `resignacion_ironica` |
|---|---|---|
| AFINN extendido con inventario emic | 0,387 | 0,511 |
| pysentimiento (detector de ironía en español) | 0,311 | 0,211 |
| **RoBERTuito ajustado (este modelo)** | **0,772** | **0,821** |

El modelo de dominio aproximadamente duplica el macro F1 del mejor método
genérico. El detector de ironía genérico clasifica la resignación irónica peor
que el método léxico, confundiéndola sistemáticamente con frustración explícita:
la ironía de esta comunidad no coincide con la ironía genérica de redes sociales,
sino que constituye un fenómeno subcultural con marcadores propios.

### Análisis de errores

Sobre los 23 errores del conjunto de prueba, la frontera teóricamente difícil
entre frustración explícita y resignación irónica está esencialmente resuelta
(solo 2 errores). Los errores se concentran en el eje de las clases con carga
afectiva hacia la clase neutral, principalmente en enunciados de resignación
irónica con marcador atenuador (p. ej. «xd») cuya superficie léxica es neutra
o positiva pese al contenido negativo, que es precisamente el mecanismo de
deflación afectiva que el modelo está diseñado para detectar.

---

## 6. Sesgos, riesgos y limitaciones

- **Léxico ofensivo en el corpus.** El material de entrenamiento contiene
  disfemismos capacitistas, insultos sexistas y homófobos, y expresiones de
  violencia hiperbólica idiomática. El modelo ha sido expuesto a este lenguaje;
  no debe usarse para generación de contenido ni en contextos donde la
  reproducción de estos sesgos pueda causar daño.
- **Violencia hiperbólica ≠ ideación.** Estadísticamente, en un corpus de más
  de 50.000 mensajes es posible que algún caso de fraseología violenta no sea
  hiperbólico. El modelo no diagnostica ni detecta riesgo y no debe sustituir
  el juicio humano en ningún escenario relacionado con la seguridad de personas.
- **Dominio específico.** El modelo está adaptado al registro de una comunidad
  concreta (*League of Legends* en español, Mediavida). Su rendimiento no está
  garantizado en otras comunidades, juegos, plataformas o variedades del español,
  y debe revalidarse antes de aplicarse fuera del dominio de entrenamiento.
- **Tamaño del subcorpus.** El ajuste fino se realizó sobre 1.200 mensajes
  anotados; la clase `otro` es minoritaria (9,4 %) y la de menor F1 (0,700).
- **Anotación por un único investigador.** La fiabilidad se garantizó por
  consistencia intra-anotador (test-retest), no por acuerdo entre múltiples
  anotadores; el esquema refleja los criterios de un solo codificador,
  documentados de forma exhaustiva en el libro de códigos.
- **Clasificación del mensaje, no del destinatario.** Véase §3.

---

## 7. Consideraciones éticas

El foro se trata como espacio público (contenido accesible sin registro;
directrices de la AoIR, 2019). Todos los recursos publicados van anonimizados.
La apertura del modelo se acompaña de las restricciones de uso de la §3 para
prevenir su aplicación en vigilancia, moderación automatizada no supervisada o
cualquier escenario de identificación o daño a usuarios individuales.

---

## 8. Cómo citar

Si utiliza este modelo, cite el TFM correspondiente y el modelo base:

- Alonso Aucejo, F. (2026). *Resignación irónica en el espacio liminal:
  evolución sociolingüística de una comunidad gamer hispanohablante. Un análisis
  diacrónico del hilo «os va el lol» en Mediavida (2010-actualidad)*. Trabajo de
  Fin de Máster,
  Máster Universitario en Ciencia de Datos aplicada a las Ciencias Sociales
  (DaSoc), Universidad de Salamanca y Universidad de Granada.
- Pérez, J. M., Furman, D. A., Alonso Alemany, L., y Luque, F. M. (2022).
  RoBERTuito: a pre-trained language model for social media text in Spanish.
  *Proceedings of the Thirteenth Language Resources and Evaluation Conference*,
  7235-7243.

---

## 9. Referencias

- Landis, J. R., y Koch, G. G. (1977). The measurement of observer agreement
  for categorical data. *Biometrics*, 33(1), 159-174.
- Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B.,
  Spitzer, E., Raji, I. D., y Gebru, T. (2019). Model Cards for Model Reporting.
  *Proceedings of the Conference on Fairness, Accountability, and Transparency
  (FAT* '19)*, 220-229.
- Pérez, J. M., Rajngewerc, M., Giudici, J. C., Furman, D. A., Luque, F.,
  Alonso Alemany, L., y Martínez, M. V. (2021). pysentimiento: A Python
  toolkit for opinion mining and social NLP tasks. *arXiv:2106.09462*.
- Pérez, J. M., Furman, D. A., Alonso Alemany, L., y Luque, F. M. (2022).
  RoBERTuito: a pre-trained language model for social media text in Spanish.
  *LREC 2022*, 7235-7243.
