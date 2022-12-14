# -*- coding: utf-8 -*-
"""SEICS_twalk_Roman.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Jlwpd6THtpS6kx1uAaRfSpWsT2jOw4NT

Importar librerías
"""

!pip install lmfit

from numpy import arange,array,dot,asarray,zeros,apply_along_axis,around,sort,shape,random,exp,empty,mean,inf,ndarray
from scipy import integrate
from matplotlib.pyplot import plot,figure,title,legend,xlabel,ylabel,grid,axvline,savefig,hist,subplots,subplot
from scipy.stats.mstats import mquantiles
from math import sqrt,log
import pandas as pd
from datetime import datetime,timedelta
from lmfit import minimize,Parameters,Parameter,report_fit
from scipy.stats import poisson,truncnorm
import scipy
from lmfit import minimize,Parameters,Parameter,report_fit
from statsmodels.graphics.tsaplots import plot_acf

!pip install kora -q
from kora import drive
drive.link_nbs()
import pytwalk

"""Implementar el modelo SEICS, agregando una variable para los casos acumulados"""

def SEICS_Model(INP,t,beta,kappa,gamma,epsilon,p):
    #Extraer las condiciones iniciales
    x=INP
    #El valor de N se definirá de forma global
    #Ecuaciones del modelo
    dS=-beta*(x[3]+x[4])*x[0]/N+epsilon*x[4]+gamma*(1-p)*x[3]
    dE=beta*(x[3]+x[4])*x[0]/N-kappa*x[1]
    #Ecuación para capturar únicamente los casos acumulados
    #dY=beta*(x[3]+x[4])*x[0]/N
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
      dif=Y_p[period*(i+1)-1]-Y_p[period*i]
      if dif>0:
        Y_inc[i]=dif
  return Y_inc

#Función objetivo para ajustar los parámetros del modelo SEIR
def residual_seics(params,x0_s,ts,datos,periodo):
    beta,kappa,gamma,epsilon,p=params['beta'].value,params['kappa'].value,params['gamma'].value,params['epsilon'].value,params['p'].value
    modelo=integrate.odeint(SEICS_Model,x0_s,ts,args=(beta,kappa,gamma,epsilon,p,))
    aprox_dia=modelo[:,2]
    aprox_sem=incidencia(aprox_dia,periodo)
    return ((aprox_sem-datos)**2).ravel()

"""#Generar datos sintéticos agregando ruido Poisson a la solución numérica del modelo"""

#Establecer datos iniciales y valores reales de los parámetros
N=100000
#Periodo de incubación de 7 a 14 días
#Del 3 al 5% son portadores asintomáticos
#Se quiere simular un R_0 entre 5 y 6
#La tasa de recuperación de los portadores asintomáticos se considerará de un año
#El periodo de recuperación es aproximadamente 3 semanas
beta,kappa,gamma,epsilon,p=3/21,0.1,1/21,1/365,0.04

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

"""#Ajuste de los parámetros mediante minimización de función objetivo

Generar datos de incidencia quincenal
"""

#Usando el mismo intervalo de tiempo, los mismos parámetros y condiciones iniciales para generar los datos sintéticos,
#por lo que sólo cambiaremos el periodo de incidencia de los casos acumulados generados
#Calcular incidencia quincenal
inc_quinc=incidencia(solucion[:,2],15)
#Número de quincenas completas en el periodo
n_quinc=int(n_days/15)

#Establecer una semilla
random.seed(seed=0)

#Agregar ruido Poisson porque son datos discretos 
data_quinc=poisson.rvs(mu=inc_quinc,size=n_quinc)

#Enumerar quincenas
t_quinc=arange(0,n_quinc,1)
figure(figsize=(12,10))
plot(t_quinc,data_quinc,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='red',label="Casos registrados")
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
estimacion1=minimize(residual_seics,params,args=(x0,t,data_quinc,periodo),method='leastsq')
estimacion1

#Extraer parámetros estimados
param_est1=estimacion1.params
print("Las estimaciones encontradas de los parámetro son:",param_est1)

#Obtener la solución del modelo con los parámetros estimados por Levenberg-Marquard
beta_est1,kappa_est1,gamma_est1,epsilon_est1,p_est1=param_est1['beta'].value,param_est1['kappa'].value,param_est1['gamma'].value,param_est1['epsilon'].value,param_est1['p'].value   
result2=integrate.odeint(SEICS_Model,x0,t,args=(beta_est1,kappa_est1,gamma_est1,epsilon_est1,p_est1,))
Y_acum2=result2[:,2]
#Incidencia quincenal del modelo ajustado
Y_quinc1=incidencia(Y_acum2,15)
#Graficar el modelo obtenido con los datos estimados contra los datos simulados
figure(figsize=(12,10))
plot(t_quinc,Y_quinc1,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='blue',label="Datos estimados")
plot(t_quinc,data_quinc,linestyle="--",marker="*",markersize=4,linewidth=0.8,color='red',label="Datos simulados")
ylabel("Número de casos")
xlabel("Número de quincena")
legend()
title("Datos Estimados con el Modelo SEICS Ajustado contra Datos Simulados")
grid()

"""#Calcular hiperparámetros con base en intervalos propuestos para cada parámetro"""

def hiper_gamma(L,U,z):
    alpha1=(z*(L+U)/(U-L))**2
    beta1=2*z**2*(L+U)/(U-L)**2
    return alpha1,beta1

def hiper_beta(L,U,z):
    alpha1=(z**2*(2-L-U)*(L+U)**2-(U-L)**2*(L+U))/(2*(U-L)**2)
    beta1=alpha1*((2-L-U)/(L+U))
    return alpha1,beta1

#Se definirán las distribuciones a priori para cada parámetro
alpha_be,beta_be=hiper_gamma(0.0,0.3,2.0)
alpha_ka,beta_ka=hiper_gamma(0,0.25,2.0)
alpha_ga,beta_ga=hiper_gamma(0,0.2,2.0)
alpha_ep,beta_ep=hiper_gamma(0.0,0.05,2.0)
alpha_p,beta_p=hiper_beta(0.0,0.1,2.0)

print("Hiperparámetros beta: ", [alpha_be,beta_be])
print("Hiperparámetros kappa: ", [alpha_ka,beta_ka])
print("Hiperparámetros gamma: ", [alpha_ga,beta_ga])
print("Hiperparámetros epsilon: ", [alpha_ep,beta_ep])
print("Hiperparámetros p: ", [alpha_p,beta_p])

"""Definir distribuciones log-a-prioris independientes para los parámetros"""

def logaprioris(theta):
    beta,kappa,gam,eps,p=theta.copy()
    log_pri_beta=scipy.stats.gamma.logpdf(beta,alpha_be,scale=1/beta_be)
    log_pri_kap=scipy.stats.gamma.logpdf(kappa,alpha_ka,scale=1/beta_ka)
    log_pri_gam=scipy.stats.gamma.logpdf(gam,alpha_ga,scale=1/beta_ga)
    log_pri_eps=scipy.stats.gamma.logpdf(eps,alpha_ep,scale=1/beta_ep)
    log_pri_p=scipy.stats.beta.logpdf(p,alpha_p,beta_p)
    return(float(log_pri_beta+log_pri_kap+log_pri_gam+log_pri_eps+log_pri_p))

"""Graficar las distribuciones a priori"""

#Se graficarán las distribuciones a priori en el intervalo [0,0.5]
fig=figure(figsize=(16,8)) 
x=arange(0,0.5,0.5/25)
priori_be=scipy.stats.gamma.pdf(x,alpha_be,scale=1/beta_be)
priori_ka=scipy.stats.gamma.pdf(x,alpha_ka,scale=1/beta_ka)
priori_ga=scipy.stats.gamma.pdf(x,alpha_ga,scale=1/beta_ga)
priori_ep=scipy.stats.gamma.pdf(x,alpha_ep,scale=1/beta_ep)
priori_p=scipy.stats.beta.pdf(x,alpha_p,beta_p)
plot(x,priori_be,'b-',label='A priori beta',color='blue')
plot(x,priori_ka,'g--',label='A priori kappa',color='green')
plot(x,priori_ga,':',label='A priori gamma',color='purple')
plot(x,priori_ep,'--',label='A priori epsilon',color='red')
plot(x,priori_p,'-.',label='A priori p',color='orange')
legend(loc="best")

"""Generar logverosimilitud suponiendo que los datos de conteo siguen una distribución Poisson, y luego generar la función de energía"""

def logverosimilitud(theta):
  beta,kappa,gam,eps,p=theta
  t_dias=arange(0,15*n_quinc,1)
  modelo=integrate.odeint(SEICS_Model,x0,t_dias,args=(beta,kappa,gam,eps,p,))
  acum_dia=modelo[:,2]
  #Incidencia quincenal
  inc_quinc=incidencia(acum_dia,15)
  #Se están teniendo problemas con los ceros, así que se removerán
  vers=zeros((n_quinc))
  for i in range(0,n_quinc):
      if inc_quinc[i]!=0 and data_quinc[i]!=0: 
          vers[i]=-inc_quinc[i]+data_quinc[i]*log(abs(inc_quinc[i]))
      elif inc_quinc[i]!=0 and data_quinc[i]==0:
          vers[i]=-inc_quinc[i]
      #Si inc_sem[i]=0 la verosimilitud de ese dato es cero
  #Sumar porque es el logaritmo de la verosimilitud
  ver=float(sum(vers))
  #print(ver)
  return(ver)  

#Distribución posterior
def posterior(theta):
    #print("1",logaprioris(theta)+logverosimilitud(theta))
    return((exp(logaprioris(theta)+logverosimilitud(theta))))

#Función de energía U=-log p(\theta| y)
def U(theta): 
    return -logaprioris(theta)-logverosimilitud(theta)

#Soporte de theta 
def Supp(theta):
    beta,kappa,gam,eps,p=theta.copy()
    if(beta>0.0 and beta<1.5 and kappa>0.0 and kappa<1.0 and gamma>0.0 and gamma<1.0 and eps>0.0 and eps<0.1 and p>0.0 and p<0.2 ):
        return True
    else:
        return False

"""#Aplicar t-walk"""

def inicializar():
  flag=False
  while flag==False:
    a=scipy.stats.gamma.rvs(alpha_be,scale=1/beta_be)
    b=scipy.stats.gamma.rvs(alpha_ka,scale=1/beta_ka)    
    c=scipy.stats.gamma.rvs(alpha_ga,scale=1/beta_ga)
    d=scipy.stats.gamma.rvs(alpha_ep,scale=1/beta_ep)    
    e=scipy.stats.beta.rvs(alpha_p,beta_p)
    tt=array([a,b,c,d,e])
    print("entra")
    if posterior(tt)>0:
      theta_ini=tt
      flag=True
  return(theta_ini)

#Generando los valores iniciales
random.seed(seed=20)
tt=inicializar()

random.seed(seed=21)
tt1=inicializar()

#tt=array([0.15,0.092,0.05,0.0031,0.046])
T=int(4*1e5) #iterations
bi=int(0.15*T)#burn in

tchain=pytwalk.pytwalk(n=5,U=U,Supp=Supp)
tchain.Run(T=T,x0=tt,xp0=tt1)

tchain.Ana()
tchain.IAT()

sims=tchain.Output[bi:,:]

"""#Resultados"""

sims.shape
for i in range(5):
  plot(sims[:,i])

"""Determinar el periodo de burnin"""

fig,ax=subplots(5,1,figsize=(20,15))
for i in range(5):
  ax[i].plot(sims[:,i])

plot_acf(sims[:,0].tolist(),lags=50);
plot_acf(sims[:,1].tolist(),lags=50);
plot_acf(sims[:,2].tolist(),lags=50);
plot_acf(sims[:,3].tolist(),lags=50);
plot_acf(sims[:,4].tolist(),lags=50);

"""#Probar con diferentes valores de saltos para adelgazar las cadenas y disminuir la autocorrelación"""

#Tamaño de muestra efectivo
def ess(data, stepSize=1):
    """ Effective sample size, as computed by BEAST Tracer."""
    samples=len(data)

    assert len(data)>1,"no stats for short sequences"
    maxLag=min(samples//3,1000)

    gammaStat=[0,]*maxLag
    varStat = 0.0;

    if type(data)!=ndarray:
        data=array(data)

    normalizedData=data-data.mean()

    for lag in range( maxLag ):
        v1=normalizedData[:samples - lag]
        v2=normalizedData[lag:]
        v=v1*v2
        gammaStat[lag]=sum(v)/len(v)
        if lag==0:
            varStat=gammaStat[0]
        elif lag%2==0:
            s=gammaStat[lag-1]+gammaStat[lag]
            if s>0:
                varStat+=2.0*s
            else:
                break

    #auto correlation time
    act=stepSize*varStat/gammaStat[0]
    # effective sample size
    ess=(stepSize*samples)/act
    return ess
    
def adelg_cadena(cad_param,saltos):
    m,n=shape(cad_param)
    m_new=int(m/saltos)
    #Matriz con las nuevas cadenas de los parámetros
    cad_new=zeros((m_new,n))
    for i in range(0,n):
        for j in range(0,m_new):
            cad_new[j,i]=cad_param[saltos*j,i]
    return cad_new

"""Adelgazamiento con saltos de 20"""

cad_adelg20=adelg_cadena(sims,20)
#Graficar autocorrelaciones las cadenas adelgazadas
plot_acf(cad_adelg20[:,0].tolist(),lags=50);
plot_acf(cad_adelg20[:,1].tolist(),lags=50);
plot_acf(cad_adelg20[:,2].tolist(),lags=50);
plot_acf(cad_adelg20[:,3].tolist(),lags=50);
plot_acf(cad_adelg20[:,4].tolist(),lags=50);

#Tamaño efectivo de la muestra
sbeta20=ess(cad_adelg20[:,0])
skappa20=ess(cad_adelg20[:,1])
sgamma20=ess(cad_adelg20[:,2])
seps20=ess(cad_adelg20[:,3])
sp20=ess(cad_adelg20[:,4])
print("Tamaño de muestra efectivo para cada parámetro: ",[sbeta20,skappa20,sgamma20,seps20,sp20])

"""Adelgazamiento con saltos de 35"""

cad_adelg35=adelg_cadena(sims,35)
#Graficar autocorrelaciones las cadenas adelgazadas
plot_acf(cad_adelg35[:,0].tolist(),lags=50);
plot_acf(cad_adelg35[:,1].tolist(),lags=50);
plot_acf(cad_adelg35[:,2].tolist(),lags=50);
plot_acf(cad_adelg35[:,3].tolist(),lags=50);
plot_acf(cad_adelg35[:,4].tolist(),lags=50);

#Tamaño efectivo de la muestra
sbeta35=ess(cad_adelg35[:,0])
skappa35=ess(cad_adelg35[:,1])
sgamma35=ess(cad_adelg35[:,2])
seps35=ess(cad_adelg35[:,3])
sp35=ess(cad_adelg35[:,4])
print("Tamaño de muestra efectivo para cada parámetro: ",[sbeta35,skappa35,sgamma35,seps35,sp35])

"""Adelgazamiento con saltos de 50"""

cad_adelg50=adelg_cadena(sims,50)
#Graficar autocorrelaciones las cadenas adelgazadas
plot_acf(cad_adelg50[:,0].tolist(),lags=50);
plot_acf(cad_adelg50[:,1].tolist(),lags=50);
plot_acf(cad_adelg50[:,2].tolist(),lags=50);
plot_acf(cad_adelg50[:,3].tolist(),lags=50);
plot_acf(cad_adelg50[:,4].tolist(),lags=50);

#Tamaño efectivo de la muestra
sbeta50=ess(cad_adelg50[:,0])
skappa50=ess(cad_adelg50[:,1])
sgamma50=ess(cad_adelg50[:,2])
seps50=ess(cad_adelg50[:,3])
sp50=ess(cad_adelg50[:,4])
print("Tamaño de muestra efectivo para cada parámetro: ",[sbeta50,skappa50,sgamma50,seps50,sp50])

"""Graficar cadenas adelgazadas"""

#Graficar las cadenas adelgazadas
fig=figure(figsize=(10,10)) 

ax1=subplot(5,1,1)
hist(cad_adelg20[:,0],14,density=True,histtype='bar',color='orange',alpha=0.6);
          
ax2=subplot(5,1,2)
hist(cad_adelg20[:,1],14,density=True,histtype='bar',color ='orange',alpha=0.6);

ax3=subplot(5,1,3)
hist(cad_adelg20[:,2],14,density=True,histtype='bar',color='orange',alpha=0.6);

ax4=subplot(5,1,4)
hist(cad_adelg20[:,3],14,density=True,histtype='bar',color ='orange',alpha=0.6);

ax5=subplot(5,1,5)
hist(cad_adelg20[:,4],14,density=True,histtype='bar',color='orange',alpha=0.6);

fig=figure(figsize=(20,10)) 
ax1=subplot(5,1,1) 
ax1.plot(cad_adelg20[:,0])
ax2=subplot(5,1,2)
ax2.plot(cad_adelg20[:,1])
ax3=subplot(5,1,3) 
ax3.plot(cad_adelg20[:,2])
ax4=subplot(5,1,4)
ax4.plot(cad_adelg20[:,3])
ax5=subplot(5,1,5)
ax5.plot(cad_adelg20[:,4])

"""#Obtener estimadores puntuales"""

#Intervalo del 95% de densidad posterior
int_beta=mquantiles(cad_adelg20[:,0],prob=[0.025,0.975])
int_kappa=mquantiles(cad_adelg20[:,1],prob=[0.025,0.975])
int_gamma=mquantiles(cad_adelg20[:,2],prob=[0.025,0.975])
int_eps=mquantiles(cad_adelg20[:,3],prob=[0.025,0.975])
int_p=mquantiles(cad_adelg20[:,4],prob=[0.025,0.975])
                 
print("Intervalo beta: ",int_beta)
print("Intervalo kappa: ",int_kappa)
print("Intervalo gamma: ",int_gamma)
print("Intervalo epsilon",int_eps)
print("Intervalo p",int_p)

#Mediana
median_be=mquantiles(cad_adelg20[:,0],prob=[0.5])
median_ka=mquantiles(cad_adelg20[:,1],prob=[0.5])
median_ga=mquantiles(cad_adelg20[:,2],prob=[0.5])
median_ep=mquantiles(cad_adelg20[:,3],prob=[0.5])
median_p=mquantiles(cad_adelg20[:,4],prob=[0.5])
print("Beta: ",median_be)
print("Kappa: ",median_ka)
print("Gamma: ",median_ga)
print("Epsilon: ",median_ep)
print("p: ",median_p)

#Media
media_be=mean(cad_adelg20[:,0])
media_ka=mean(cad_adelg20[:,1])
media_ga=mean(cad_adelg20[:,2])
media_ep=mean(cad_adelg20[:,3])
media_p=mean(cad_adelg20[:,4])
print("Beta: ",media_be)
print("Kappa: ",media_ka)
print("Gamma: ",media_ga)
print("Epsilon: ",media_ep)
print("p: ",media_p)

#Moda
moda_be=max(cad_adelg20[:,0])
moda_ka=max(cad_adelg20[:,1])
moda_ga=max(cad_adelg20[:,2])
moda_ep=max(cad_adelg20[:,3])
moda_p=max(cad_adelg20[:,4])
print("Beta: ",moda_be)
print("Kappa: ",moda_ka)
print("Gamma: ",moda_ga)
print("Epsilon: ",moda_ep)
print("p: ",moda_p)

"""Curvas de incidencia quincenal para los estimadores mediana, moda y media"""

model_median=integrate.odeint(SEICS_Model,x0,t,args=(median_be[0],median_ka[0],median_ga[0],median_ep[0],median_p[0],))
Y_acum_median=model_median[:,2]
inc_median=incidencia(Y_acum_median,15)

model_media=integrate.odeint(SEICS_Model,x0,t,args=(media_be,media_ka,media_ga,media_ep,media_p,))
Y_acum_media=model_media[:,2]
inc_media=incidencia(Y_acum_media,15)

model_moda=integrate.odeint(SEICS_Model,x0,t,args=(moda_be,moda_ka,moda_ga,moda_ep,moda_p,))
Y_acum_moda=model_moda[:,2]
inc_moda=incidencia(Y_acum_moda,15)

#Graficar el modelo obtenido con los datos estimados contra los datos registrados
figure(figsize=(12,10))
plot(t_quinc,inc_median,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='blue',label="Estimación con la mediana")
plot(t_quinc,inc_media,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='orange',label="Estimación con la media")
plot(t_quinc,inc_moda,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='darkgreen',label="Estimación con la moda")
plot(t_quinc,data_quinc,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='red',label="Casos registrados")
ylabel("Número de casos")
xlabel("Número de quincena")
legend()
title("Estimaciones con el modelo SEICS contra datos simulados")
grid()

"""Banda del 90% de densidad posterior"""

#Intervalo del 90% de densidad posterior
int_beta1=mquantiles(cad_adelg20[:,0],prob=[0.05,0.95])
int_kappa1=mquantiles(cad_adelg20[:,1],prob=[0.05,0.95])
int_gamma1=mquantiles(cad_adelg20[:,2],prob=[0.05,0.95])
int_eps1=mquantiles(cad_adelg20[:,3],prob=[0.05,0.95])
int_p1=mquantiles(cad_adelg20[:,4],prob=[0.05,0.95])

print("Intervalos del 90% de densidad posterior")
print("Beta:",int_beta1)
print("Kappa:",int_kappa1)
print("Gamma:",int_gamma1)
print("Epsilon:",int_eps1)
print("p:",int_p1)

#Tamaño de paso para ir recorriendo los intervalores al 90% de densidad posterior de los parámetros

beta_inf,beta_sup=int_beta1[0],int_beta1[1]
kappa_inf,kappa_sup=int_kappa1[0],int_kappa1[1]
gamma_inf,gamma_sup=int_gamma1[0],int_gamma1[1]
eps_inf,eps_sup=int_eps1[0],int_eps1[1]
p_inf,p_sup=int_p1[0],int_p1[1]

h1,h2,h3,h4,h5=(beta_sup-beta_inf)/5.0,(kappa_sup-kappa_inf)/5.0,(gamma_sup-gamma_inf)/5.0,(eps_sup-eps_inf)/5.0,(p_sup-p_inf)/5.0

#Número total de curvas
m1=6**6
curvas=zeros((m1,n_quinc))
cont=0
#Consideranto los cuantiles de 90% de probabilidad para cada uno de los tres parámetros
for i in range(0,6):
    for j in range(0,6):
        for k in range(0,6): 
            for l in range(0,6):
                for s in range(0,6):
                    solucion=integrate.odeint(SEICS_Model,x0,t,args=(beta_inf+i*h1,kappa_inf+i*h2,gamma_inf+i*h3,eps_inf+i*h4,p_inf+i*h5,))
                    casos_acum=solucion[:,2]
                    curvas[cont,:]=incidencia(casos_acum,15)
                    cont+=1

figure(figsize=(18, 9))
for i in range(0,m1):
    plot(t_quinc,curvas[i,:],color="grey",alpha=0.5)
plot(t_quinc,inc_median,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='blue',label="Estimación con la mediana")
plot(t_quinc,inc_media,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='orange',label="Estimación con la media")
plot(t_quinc,inc_moda,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='green',label="Estimación con la moda")
plot(t_quinc,data_quinc,linestyle="--",marker="o",markersize=4,linewidth=0.8,color='red',label="Casos registrados")
ylabel("Número de casos")
xlabel("Número de semana")
legend()
title("Banda del 90% de densidad posterior")
grid()

