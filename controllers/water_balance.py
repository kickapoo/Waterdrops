import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
from pylab import *
font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 12}
matplotlib.rc('font', **font)
####################




def wb_data():
	waterdrop_id = request.args(0,cast = int)
	waterdrop = db.waterdrop[request.args(0,cast =int)]
	sensors_types = db((db.sensors.waterdrop ==  waterdrop_id) & \
		((db.sensors.sensor_type == "Rainfall") | (db.sensors.sensor_type == "Temperature")) \
			).select()
	message_control = " "
	rainfalls =[row.station.name for row in sensors_types if row.sensor_type == "Rainfall"]
	temps =[row.station.name for row in sensors_types if row.sensor_type == "Temperature"]
	if len(sensors_types) >=  1:
		message_control = "You have at least one Rain/Temp Sensor"
	else:
		session.flash  = "You must have at least one Rainfall and Temperature Sensor!!!"
		redirect(URL('profile','index',args = waterdrop_id))

	form = SQLFORM.factory(
		Field('r_stations',label = "Select Rainfall Sensors", notnull=True, requires=IS_IN_SET(rainfalls,multiple=True),widget= horizontal_radios),
		Field('t_stations',label = "Select Temperature Sensors",notnull=True, requires=IS_IN_SET(temps,multiple=True),widget=horizontal_radios),
		Field('CN','double',default = 78),
		Field('S','double',default = 20,label ="Initial Soil Conditions")
		).process(keepvalues = True)
	rains = ''
	temps = ''
	if form.accepted:
		rains = form.vars.r_stations
		temps = form.vars.t_stations
		#Pass list for gathering sensors for spatial mean... 
		redirect(URL('water_balance','balance_calc',vars = {"rains":rains,"temps":temps,'id' :waterdrop_id, 'CN':form.vars.CN,'S':form.vars.S}))
	elif form.errors:
		response.flash = "..Check entered values"
	else:
		response.flash = ""
	
	return dict(rains = rains,temps = temps,form = form,message_control = message_control,\
		waterdrop=waterdrop)

def horizontal_radios(f,v): 
	#making Chechboxes Inline display
    table = SQLFORM.widgets.checkboxes.widget(f,v) 
    rows = table.elements('tr') 
    table.components = [] 
    table.append([row.elements('td') for row in rows]) 
    return table


def balance_calc():
	stations_rains = request.vars.rains
	stations_temps = request.vars.temps
	waterdrop_id    = request.vars.id
	waterdrop = db.waterdrop[request.vars.id]
	K = 25.4 * ((1000/float(request.vars.CN)) -10)
	S = float(request.vars.S)
	rainsensors = db((db.sensors.waterdrop == waterdrop_id) & (db.sensors.sensor_type == "Rainfall")).select(db.sensors.station,db.sensors.myfile, db.sensors.sensor_type)
	tempsensors = db((db.sensors.waterdrop == waterdrop_id) & (db.sensors.sensor_type == "Temperature")).select(db.sensors.station,db.sensors.myfile, db.sensors.sensor_type)
	
	#Rains 
	months_rains = read_dfs(rainsensors,stations_rains,"sum")
	over_rains_stats = months_rains.describe()
	plot_rains_month = plot3_bar(months_rains.index,months_rains,'',' ','mm')
	#Temps
	month_temps = read_dfs(tempsensors,stations_temps,"mean")
	over_temps_stats = month_temps.describe()
	plot_temps_month = plot3_bar(month_temps.index,month_temps,'','','oC')

	#Thornthwaite Mean
	evapTh = pd.DataFrame(month_temps)
	evapTh['j'] = evapTh['mean'].apply(lambda x: 0.09*(x**(3/2)))
	evapTh['J'] = ''
	for index in evapTh.index:
		evapTh['J'][str(index.year)] = evapTh['j'][str(index.year)].sum()
	
	evapTh['a']=evapTh['J'].apply(lambda x: 0.016*x+0.5)

	def thornthwaite2(J,T,a,m,N):
		return 16*((10*T/J)**a)*(m*N/360)

	evapTh['Thornthwaite2'] = ''

	daylight = 12
	for index, row in evapTh.iterrows():
		evapTh['Thornthwaite2'] = thornthwaite2(evapTh['J'],evapTh['mean'],evapTh['a'],index.day,daylight)
	#EVAP results

	evap = evapTh['Thornthwaite2'] 
	month_th = evap.describe()
	plot_evap_month = plot3_bar(evap.index,evap,'','','mm')

	# ######################Save Data - Give Link to Download#########################
	d = {'rains':months_rains,'temps':month_temps,'evap' : evap}
	data=pd.DataFrame(d)
	# Model
	dataclear = data.dropna()
	index_plot = [item for item in dataclear.index]
	rains = [item for item in dataclear.rains]
	evaps = [item for item in dataclear.evap]
	#Water balance Model with not nan
	soil_storage = []
	q = []
	for  index,data in enumerate(zip(rains,evaps)):
	    if data[0]>data[1]:
	        S = min(S + data[0]-data[1],K)
	        soil_storage.append(S)
	        Q = max(S+data[0]-data[1]-K,0)
	        q.append(Q)
	    else:
	        S = S*math.exp((data[0]-data[1]) / K)
	        soil_storage.append(S)
	        Q = 0
	        q.append(Q) 
	#Plot Q 
	plot_q = plot3(index_plot,q,'Surface Water Flow ','','mm',12)
	#Plot Soil
	plot_soil = plot3(index_plot,soil_storage,'Soil Water Storage ','','mm',12)
	return dict(months_rains = months_rains,over_rains_stats = over_rains_stats, \
		month_temps = month_temps,over_temps_stats = over_rains_stats,\
		month_th=month_th, plot_evap_month = plot_evap_month, \
		plot_rains_month = plot_rains_month,plot_temps_month = plot_temps_month,\
		plot_q=plot_q,plot_soil=plot_soil, waterdrop = waterdrop)


#Multi: Read stations, takes means, plots them and return df_new['mean']
def read_dfs(files_db,stations_names,hows="sum"):
	dfs = {}
	for files_db,name in zip(files_db,stations_names):
		file_name = files_db.myfile 
		file_path = os.path.join(request.folder,'uploads',file_name)
		data = pd.read_csv(file_path, skiprows = [num for (num,line) in enumerate(open(file_path),2) if 'Precision=' in line][0],
                 parse_dates =  True,index_col = 0,header= None, sep =',',names = ['meteo', 'empty'])
		dfs[name] = data.meteo.resample('M',how = hows)
	df_new = pd.DataFrame(dfs)
	df_new['mean'] = df_new.mean(1)
	return df_new['mean']

#Plot Bar 
def plot3_bar(data_index,data,title,xlabel,ylabel, size = 8):
	import mpld3
	fig, ax = plt.subplots(figsize=(size, 4),sharey=True, sharex=True)
	ax.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
	ax.bar(data_index,data)
	ax.set_title(title)
	ax.set_xlabel(xlabel)
	ax.set_ylabel(ylabel)
	make_html = mpld3.fig_to_html(fig, template_type = "general")
	return make_html

def plot3(data_index,data,title,xlabel,ylabel, size = 8):
	import mpld3
	fig, ax = plt.subplots(figsize=(size, 4),sharey=True, sharex=True)
	ax.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
	ax.plot(data_index,data)
	ax.set_title(title)
	ax.set_xlabel(xlabel)
	ax.set_ylabel(ylabel)
	make_html = mpld3.fig_to_html(fig, template_type = "general")
	return make_html

#Plot Histogram with Cumulutive
def hist_cum3_plot(data):
	# A histogram
	fig, ax = plt.subplots(1, 2, figsize=(12,4))
	ax[0].grid(True, alpha=0.5)
	ax[0].hist(data)
	ax[0].set_title("Default histogram")
	ax[0].set_xlim((min(data), max(data)))
	ax[1].hist(data, cumulative=True, bins=50)
	ax[1].grid(True, alpha=0.5)
	ax[1].set_title("Cumulative detailed histogram")
	ax[1].set_xlim((min(data), max(data)));
	make_html = mpld3.fig_to_html(fig, template_type = "general")
	return make_html

















