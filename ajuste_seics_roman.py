# -*- coding: utf-8 -*-
"""Ajuste_SEICS_Roman.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ufyu4zJ0UA8dH9WV77SXfPZejCp5QHGU

Importar librerías
"""

!pip install lmfit

from matplotlib.pyplot import plot,figure,title,legend,scatter
from numpy import arange,array,dot,asarray,zeros,apply_along_axis,around,sort,shape,random
from scipy import integrate
from matplotlib.pyplot import plot,figure,title,legend,xlabel,ylabel,grid,axvline,savefig
from math import sqrt
import pandas as pd
from datetime import datetime,timedelta
from lmfit import minimize,Parameters,Parameter,report_fit
from scipy.stats import poisson
from sklearn.metrics import mean_squared_error,mean_absolute_percentage_error

"""Implementar el modelo SEICS, agregando una variable para los casos acumulados"""

def SEICS_Model(INP,t,beta,kappa,gamma,epsilon,p):
    #Extraer las condiciones iniciales
    x=INP
    #El valor de N se definirá de forma global
    #Ecuaciones del modelo
    dS=-beta*(x[3]+x[4])*x[0]/N+epsilon*x[4]+gamma*(1-p)*x[3]
    dE=beta*(x[3]+x[4])*x[0]/N-kappa*x[1]
    #Ecuación para capturar únicamente los casos acumulados
    dY=kappa*x[1]
    dI=kappa*x[1]-gamma*x[3]
    dC=gamma*p*x[3]-epsilon*x[4]
    return dS,dE,dY,dI,dC

#Calcular la incidencia en el periodo de días indicado a partir de casos acumulados
def incidencia(Y_p,period):
  #Número de días
  n=len(Y_p)
  #Número de semanas
  m=int(n/period)
  Y_inc=zeros((m))
  Y_inc[0]=Y_p[period-1]
  for i in range(1,m):
      Y_inc[i]=Y_p[period*(i+1)-1]-Y_p[period*i]
  return Y_inc

#Calcular el número reproductivo básico
def calcular_R0(beta,gamma,epsilon,p):
    R0=beta/gamma+beta*p/epsilon
    return R0

#Punto de equilibrio endémico
def equi_end(beta,kappa,gamma,epsilon,p):
    R0=calcular_R0(beta,gamma,epsilon,p)
    S_1=N/R0
    I_1=beta*N*(R0-1)/(gamma*R0*(R0+beta/kappa))
    E_1=gamma*I_1/kappa
    C_1=gamma*p*I_1/epsilon
    return [S_1,E_1,I_1,C_1]

#Función objetivo para ajustar los parámetros del modelo SEIR
def residual_seics(params,x0_s,ts,datos,periodo):
    beta,kappa,gamma,epsilon,p=params['beta'].value,params['kappa'].value,params['gamma'].value,params['epsilon'].value,params['p'].value
    modelo=integrate.odeint(SEICS_Model,x0_s,ts,args=(beta,kappa,gamma,epsilon,p,))
    aprox_dia=modelo[:,2]
    aprox_sem=incidencia(aprox_dia,periodo)
    return ((aprox_sem-datos)**2).ravel()

"""Generar datos sintéticos agregando ruido Poisson a la solución numérica del modelo"""

#Establecer datos iniciales y valores reales de los parámetros
N=100000
#Periodo de incubación de 7 a 14 días
#Del 3 al 5% son portadores asintomáticos
#Se quiere simular un R_0 entre 5 y 6
#La tasa de recuperación de los portadores asintomáticos se considerará de un año
#El periodo de recuperación es aproximadamente 3 semanas
beta,kappa,gamma,epsilon,p=3/21,0.1,1/21,1/365,0.04
#El R_0 considerado es el siguiente
R_0=calcular_R0(beta,gamma,epsilon,p)
print("El R0 considerado para generar los datos es de:",R_0)
#Punto de equilibrio endémico
punto_end=equi_end(beta,kappa,gamma,epsilon,p)
print("El punto de equilibrio endémico se alcanza en: ",punto_end)

#Considerar un periodo de 420 días para un total de 60 semanas
n_days=840
t=arange(0,n_days,1)
#Condiciones iniciales
#Se supondrá que al inicio del estudio se tienen 25 infectados de fiebre tifoidea
E0=0
I0=25
C0=0
Y0=I0
#La población es cerrada
S0=N-E0-I0-C0
#Poner todas las condiciones iniciales en una lista
x0=[S0,E0,Y0,I0,C0]
#Obtener la solución del sistema con estos parámetros y condiciones iniciales
solucion=integrate.odeint(SEICS_Model,x0,t,args=(beta,kappa,gamma,epsilon,p,))
#Calcular incidencia semanal
inc_sem=incidencia(solucion[:,2],7)
n_sem=int(n_days/7)

#Establecer una semilla
random.seed(seed=233423)

#Agregar ruido Poisson porque son datos discretos 
datos_sem_ruido=poisson.rvs(mu=inc_sem,size=n_sem)

"""Graficar incidencia semanal con ruido Poisson"""

#Enumerar semanas
t_sem=arange(0,n_sem,1)
figure(figsize=(12,10))
plot(t_sem,datos_sem_ruido,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='red',label="Casos registrados")
ylabel("Número de casos")
xlabel("Número de semana")
legend()
title("Incidencia semanal de casos de Fiebre Tifoidea")
grid()

"""Ajuste de los parámetros mediante minimización de función objetivo"""

#Posibles rangos para los parámetros
params=Parameters()
#beta,kappa,gamma,epsilon,p=3/21,0.1,1/21,1/365,0.04
params.add('beta',value=0.2,min=0,max=0.5)
params.add('kappa',value=0.2,min=0,max=0.5)
params.add('gamma',value=0.1,min=0,max=0.5)
params.add('epsilon',value=0.01,min=0,max=0.1)
params.add('p',value=0.1,min=0,max=0.2)

#Ajustar el modelo y estimar los parámetros usando por Levenberg-Marquard
#Se utilizará incidencia semanal
periodo=7
estimacion=minimize(residual_seics,params,args=(x0,t,datos_sem_ruido,periodo),method='leastsq')
estimacion

#Extraer parámetros estimados
param_est=estimacion.params
print("Las estimaciones encontradas de los parámetro son:",param_est)

#Obtener la solución del modelo con los parámetros estimados por Levenberg-Marquard
beta_est,kappa_est,gamma_est,epsilon_est,p_est=param_est['beta'].value,param_est['kappa'].value,param_est['gamma'].value,param_est['epsilon'].value,param_est['p'].value   
result1=integrate.odeint(SEICS_Model,x0,t,args=(beta_est,kappa_est,gamma_est,epsilon_est,p_est,))
Y_acum1=result1[:,2]
#Incidencia semanal del modelo ajustado
Y_sem1=incidencia(Y_acum1,7)
#Graficar el modelo obtenido con los datos estimados contra los datos simulados
figure(figsize=(12,10))
plot(t_sem,Y_sem1,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='blue',label="Datos estimados")
plot(t_sem,datos_sem_ruido,linestyle="--",marker="*",markersize=4,linewidth=0.8,color='red',label="Datos simulados")
ylabel("Número de casos")
xlabel("Número de semana")
legend()
title("Datos Estimados con el Modelo SEICS Ajustado contra Datos Simulados")
grid()

#Calcular R0 asociado al modelo ajustado
R_0_new=calcular_R0(beta_est,gamma_est,epsilon_est,p_est)
print("El R0 asociado al modelo ajustado es:", R_0_new)

#Calcular el error cuadrático medio entre los datos sintéticos y los datos predichos
error_sem=mean_absolute_percentage_error(datos_sem_ruido,Y_sem1)
print("El error porcentual promedio de este ajuste es de:",error_sem)

"""Generar datos con incidencia quincenal"""

#Usando el mismo intervalo de tiempo, los mismos parámetros y condiciones iniciales para generar los datos sintéticos,
#por lo que sólo cambiaremos el periodo de incidencia de los casos acumulados generados
#Calcular incidencia quincenal
inc_quinc=incidencia(solucion[:,2],15)
#Número de quincenas completas en el periodo
n_quinc=int(n_days/15)

#Establecer una semilla
random.seed(seed=0)

#Agregar ruido Poisson porque son datos discretos 
datos_quinc_ruido=poisson.rvs(mu=inc_quinc,size=n_quinc)

#Enumerar quincenas
t_quinc=arange(0,n_quinc,1)
figure(figsize=(12,10))
plot(t_quinc,datos_quinc_ruido,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='red',label="Casos registrados")
ylabel("Número de casos")
xlabel("Número de quincena")
legend()
title("Incidencia quincenal de casos de Fiebre Tifoidea")
grid()

"""Ajuste de los parámetros mediante minimización de función objetivo"""

#Posibles rangos para los parámetros
params=Parameters()
#beta,kappa,gamma,epsilon,p=3/21,0.1,1/21,1/365,0.04
params.add('beta',value=0.2,min=0,max=0.5)
params.add('kappa',value=0.2,min=0,max=0.5)
params.add('gamma',value=0.1,min=0,max=0.5)
params.add('epsilon',value=0.01,min=0,max=0.1)
params.add('p',value=0.1,min=0,max=0.2)

#Ajustar el modelo y estimar los parámetros usando por Levenberg-Marquard
#Se utilizará incidencia quincenal
periodo=15
estimacion1=minimize(residual_seics,params,args=(x0,t,datos_quinc_ruido,periodo),method='leastsq')
estimacion1

#Extraer parámetros estimados
param_est1=estimacion1.params
print("Las estimaciones encontradas de los parámetro son:",param_est)

#Obtener la solución del modelo con los parámetros estimados por Levenberg-Marquard
beta_est1,kappa_est1,gamma_est1,epsilon_est1,p_est1=param_est1['beta'].value,param_est1['kappa'].value,param_est1['gamma'].value,param_est1['epsilon'].value,param_est1['p'].value   
result2=integrate.odeint(SEICS_Model,x0,t,args=(beta_est1,kappa_est1,gamma_est1,epsilon_est1,p_est1,))
Y_acum2=result2[:,2]
#Incidencia quincenal del modelo ajustado
Y_quinc1=incidencia(Y_acum2,15)
#Graficar el modelo obtenido con los datos estimados contra los datos simulados
figure(figsize=(12,10))
plot(t_quinc,Y_quinc1,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='blue',label="Datos estimados")
plot(t_quinc,datos_quinc_ruido,linestyle="--",marker="*",markersize=4,linewidth=0.8,color='red',label="Datos simulados")
ylabel("Número de casos")
xlabel("Número de quincena")
legend()
title("Datos Estimados con el Modelo SEICS Ajustado contra Datos Simulados")
grid()

#Parámetros reales
#beta,kappa,gamma,epsilon,p=3/21,0.1,1/21,1/365,0.04
#Calcular R0 asociado al modelo ajustado
R_0_new1=calcular_R0(beta_est1,gamma_est1,epsilon_est1,p_est1)
print("El R0 asociado al modelo ajustado es:", R_0_new1)

#Calcular el error cuadrático medio entre los datos sintéticos y los datos predichos
error_quinc=mean_absolute_percentage_error(datos_quinc_ruido,Y_quinc1)
print("El error porcentual promedio de este ajuste es de:",error_quinc)