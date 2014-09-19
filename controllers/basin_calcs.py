import math
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import numpy as np
from pylab import *
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 12}
matplotlib.rc('font', **font)



def qmax():
	area = db.basins[request.args(0,cast=int)].area
	name = db.basins[request.args(0,cast=int)].name
	A  = float(area) #Km2 / Catchment Area
	q1 = 24.14*(A**0.516)
	q2 = 5.5 * (A**(5/6))
	q3 = 13.8 * (A**0.6)
	q4 = A * (30/(A**0.5))
	return dict(area=area,name=name,A=A,q1=q1,q2=q2,q3=q3,q4=q4)


def indices():
	basin = db.basins[request.args(0,cast=int)]
	name = db.basins[request.args(0,cast=int)].name
	A = basin.area
	L = basin.river_lenght
	P = basin.perimeter
	compactness = P/(2*math.sqrt(3.14*A))
	form_factor = A/L
	circularity = (4*3.14*A)/(P**2)
	elongation  = 2*math.sqrt((A/3.14)/L)
	return dict(basin=basin,name=name,A=A,L=L,P=P,compactness = round(compactness,2),\
		form_factor = round(form_factor,2),circularity = round(circularity,2),\
		elongation= round(elongation,2))


def tc():
	basin = db.basins[request.args(0,cast=int)]
	name = db.basins[request.args(0,cast=int)].name
	A = basin.area
	L = basin.river_lenght
	Hmax = basin.hmax
	Hmin = basin.hmin
	Giandotti = (4*math.sqrt(A)+1.5*L)/(0.8 * math.sqrt(Hmax-Hmin))
	SCS = (L*3280.84**1.15)/(7700*((Hmax-Hmin)**0.38))
	return dict(basin=basin, name = name, A=A,L=L,Hmax=Hmax,Hmin=Hmin,Giandotti = round(Giandotti,2),\
		SCS = round(SCS,2))

def snyder_calc():
	basin = db.basins[request.args(0,cast=int)]
	name = db.basins[request.args(0,cast=int)].name
	A = basin.area#Km2 / Catchment Area
	L = basin.river_lenght # km / Main River Lenght
	SUH = ''
	a   = ''
	make_html = ''
	form = SQLFORM.factory(
		Field('Lc','double',default = "3.75",comment = "Distance of Catchment exit from Catchment Centroid"),
		Field('Ct','double',default = "1.6", comment ="Regional Factor , values range 1.0  - 2.2"),
		Field('Cp','double',default = "0.65",comment = "Regional Factor, values range 0.3 - 0.93"),
		Field('tR','double', default = "0.25",comment = "Selected Rainfall Excess duration in hr ex 30 min = 0.5 hr")
		).process(keepvalues = True)
	if form.accepted:
		#Lc = 3.75 # km / Distance of Catchment exit from Catchment Centroid
		#Ct = 1.6  # Regional Factor, values range  1.0 - 2.2
		#Cp = 0.65 # Regional Factor, values range  0.3 - 0.93
		#tR = 0.25 # Selected Rainfall Excess duration in hr ex 30 min = 0.5 hr
		SUH = shyder_unit(A,L,form.vars.Lc,form.vars.Ct,form.vars.Cp,form.vars.tR)
		#Plot Interactive
		import matplotlib.pyplot as plt, mpld3
		fig, ax = plt.subplots()
		plot = ax.plot(list(SUH['plot_t']),list(SUH['plot_Q']), 'ks-', mec='w', mew=5, ms=20)
		plt.vlines(SUH['plot_t'][3],SUH['plot_Q'][3],0, color='DarkOrange', linestyle='dashed', lw=2)
		plt.text(SUH['plot_t'][3],SUH['plot_Q'][3], 'QPR')
		plt.hlines(SUH['plot_Q'][2],SUH['plot_t'][2],SUH['plot_t'][4], color='DarkOrange', linestyle='dashed', lw=2)
		plt.text(SUH['plot_t'][4]+0.3, SUH['plot_Q'][2], 'W75')
		plt.hlines(SUH['plot_Q'][1],SUH['plot_t'][1],SUH['plot_t'][5], color='DarkOrange', linestyle='dashed', lw=2)
		plt.text(SUH['plot_t'][5]+0.3, SUH['plot_Q'][1], 'W50')
		plt.hlines(SUH['QPR']+0.5, 0, SUH['tr'],color='Blue', lw=15)
		plt.hlines(SUH['QPR']+0.5,SUH['tr']/2,SUH['plot_t'][3],color='DarkOrange', linestyle='-.',lw=2.5)
		plt.text(0.5,SUH['QPR'], 'tR  '+str(SUH['tR'])+'  hr')
		plt.text(SUH['Tb']/2, 0.5, 'Base time: '+ str(SUH['Tb'])+' hr')
		plt.hlines(0,0, SUH['Tb'],color='DarkOrange', linestyle='dashed',lw = 5)
		plt.title('Snyder Synthetic Unit Hydrograph')
		plt.xlabel('t (hr)')
		plt.ylabel('Q m3/sec')
		plt.grid()
		make_html = mpld3.fig_to_html(fig, template_type = "general")
		#plot = plot_SUH(SUH)
	elif form.errors:
		response.flash = "form has errors"
	else:
		response.flash = "please fill out the form"
	return locals()

##this must not be URL request NEVER
def shyder_unit(A,L,Lc,Ct=2.0,Cp=0.65, tR =0.5):
	C1 = 1.0 # Unit Conversion Factor
	tp = C1*Ct*((L*0.621371)*(Lc*0.621371))**0.3 #standard unit hydrograph the basin lag
	tr=tp/5.5 #effective rainfall duration
	tPR = tp + 0.25*(tR-tr) #  standard unit hydrograph for Selected Rainfall Excess Duration 
	QPR = 2.75*Cp*(A)/tPR  # peak discharge of the required UH
	W50 = 2.14/(QPR/A)**1.08 #widths of the UH at values of 50% (W50)  of qpR
	W75 = 1.22/(QPR/A)**1.08 #widths of the UH at values of 75% (W75) of qpR
	Tb = 11.11*(A/QPR) - 1.5*W50 - W75 #base time of the required UH
	T = 3 + 3*(tPR/24) #base time of the required UH in day Mimikou pag.207 formula
	plot_t = np.array([0, (tr/2+tPR)-W50/3,(tr/2+tPR)-W75/3,tr/2+tPR,(tr/2+tPR)+ W75/3,(tr/2+tPR) + W50/3, Tb])
	plot_Q = np.array([0, QPR*0.5, QPR*0.75, QPR, QPR*0.75, QPR*0.5, 0])
	return dict(tp=tp,tr=round(tr,2),tPR=round(tPR,2),QPR=round(QPR,2),W50=round(W50,2), W75=round(W75,2),Tb=round(Tb,2),plot_t=plot_t,plot_Q=plot_Q, tR=tR)

