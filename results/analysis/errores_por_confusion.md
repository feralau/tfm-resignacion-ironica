# Análisis de errores del clasificador

Total ejemplos test: 120. Errores: 23 (19.2%).

## frustracion_explicita → neutral  (7 casos)

- **msg 50554**: «se ha ido a la puta?»
- **msg 22335**: «mierda de lol ami tmb me ha petado»
- **msg 23989**: «yo llevo 10 minutos esperando para entrar a una normal y no me empareja con nadie... creo que esto ha petado de nuevo chicos»
- **msg 49546**: «hola buenas el ratón y el cursor me funcionan bien, pero cuando entro en partida me deja de funcionar en el cliente y cuando entro a partida el cursor ni si quiera se ve aunque si puedo ciclar, pero no puedo . lo he desinstalado varias veces pero nada!!! estoy desesperado ayuda por favor gente de lo»
- **msg 48011**: «lo que no entiendo es que mi equipo no haya tirado de remake cuando se me ha caído... no creo que hayan hecho firstblood lol»
- **msg 46777**: «sigo con los picos de ping de 500ms me joden partidas :s»
- **msg 1499**: «28 min en cola. el servidor del lol es un pentium 1?»

## resignacion_ironica → neutral  (4 casos)

- **msg 750**: «cada día va peor xd»
- **msg 44432**: «pues yo acabo de entrar y solo tenia 5 minutos de cola. parece que se me da bien chupar...»
- **msg 40290**: «me acaba de petar y el servidor aparece como no disponible xd»
- **msg 761**: «otra vez se cayo, muy bien, hasta luego.»

## neutral → otro  (3 casos)

- **msg 39133**: «thereisnourflevel op»
- **msg 44312**: «codigo konami y a ludar xd»
- **msg 5013**: «alguien me explica lo que es "el konami" ?»

## otro → resignacion_ironica  (2 casos)

- **msg 21629**: «goes»
- **msg 16553**: «the server is busy pussy»

## neutral → frustracion_explicita  (2 casos)

- **msg 50352**: «laggspikes de bajar de 39/40 de ping a 500 y pico por toda la cara. movistar. alguien sabe decirme si es el server o el distribuidor? en base a su experiencia vaya»
- **msg 45456**: «[cita] pues igual asi estas una hora, y esperate que no vuelva a pasar en la siguiente partida como me paso a mi xd de 6 partidas que jugue ayer 2 se fueron a tomar por culo de forma consecutiva.»

## neutral → resignacion_ironica  (2 casos)

- **msg 746**: «si era clasificatoria decir bye bye a los puntos»
- **msg 32552**: «[cita] a joder, estoy empanao xd ty»

## frustracion_explicita → otro  (1 casos)

- **msg 45538**: «[cita] 1º riot no te lee. 2º el juego es gratis, si no te gustan las caidas del server no juegues. 3º los afks forman parte de la mierda de la comunidad del lol. 4º necesitas asomar la cabeza por la ventana para que te de el aire y relajarte un poco.»

## resignacion_ironica → frustracion_explicita  (1 casos)

- **msg 23164**: «coraje maxo tengo una conex xcule, pa una dia q va bien se jode el lol xd»

## frustracion_explicita → resignacion_ironica  (1 casos)

- **msg 50220**: «y aun se plantean dejar el clash cuando no pueden ni mantener el servidor xd»

## Interpretación pendiente

Para cada par de confusión frecuente:

- ¿Qué tienen en común los mensajes mal clasificados?
- ¿Es un fallo del modelo o una ambigüedad genuina del mensaje?
- ¿Sugiere un refinamiento del codebook o del preprocesador?
- ¿Hay un patrón temporal (una fase concentra más errores)?
