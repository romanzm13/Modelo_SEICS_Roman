# Modelo_SEICS_Roman
Ajuste cuadrático e inferencia bayesiana del modelo SEICS propuesto
1. Se presenta un modelo epidemiológico compartimental para la fiebre tifoidea denominado SEICS.
2. En el archivo ajuste_seics_roman se encuentra dicho modelo implementado y se generan datos de sintéticos de incidencia semanal y quincenal usando la solución numérica
del modelo y agregando ruido Poisson. Luego se hace un ajuste del modelo minimizando la función de pérdida cuadrática a través del algoritmo Levenberg-Marquardt.
3. Por otro lado, en el archivo seics_twalk_roman.py se realiza la inferencia bayesiana del modelo. Se generan las cadenas de las distribuciones posteriores de los 
parámetros del modelo usando la paquetería implementada por el Dr. Andrés Christen y que se encuentra en el archivo pytwalk.py.
4. Así, se calcula el tamaño de muestra efectivo, se hace adelgazamiento de las cadenas resultantes y se realizan estimaciones puntuales y por intervalos de los parámetros
de interés.
