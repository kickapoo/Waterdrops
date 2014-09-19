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
import mpld3



#All sensors & time periods 
def all_periods_sensors():
	waterdrop_id =  request.args(0,cast =int)
	sensors = ''
	#Form to select result 
	form = SQLFORM.factory(Field('meteo_var',requires = IS_IN_SET(meteo_vars), label = "Select Sensor Type")
		).process()
	if form.accepted:
		sensors = db((db.sensors.waterdrop == waterdrop_id) \
			& (db.sensors.sensor_type == form.vars.meteo_var)).select()
	return dict(sensors = sensors,form = form, file_dates = file_dates)

#All stations Periods
def all_periods_stations():
	waterdrop_id =  request.args(0,cast =int)
	sensors = db(db.sensors.waterdrop == waterdrop_id).select(orderby= db.sensors.station.name)
	return dict(sensors = sensors, file_dates = file_dates)


def file_dates(var_file):
	file_path  = os.path.join(request.folder,'uploads',var_file)
	df = pd.read_csv(file_path, skiprows = [num for (num,line) in enumerate(open(file_path),2) if 'Precision=' in line][0],
                 parse_dates =  True,index_col = 0,header= None, sep =',',
                 names = ['meteo', 'empty'])
	start = df.meteo.first_valid_index()
	finish = df.meteo.last_valid_index()
	return dict(start=start,finish=finish)


def one_file_read(var_file):
	file_path = os.path.join(request.folder,'uploads',var_file)
	df = pd.read_csv(file_path, skiprows = [num for (num,line) in enumerate(open(file_path),2) if 'Precision=' in line][0],
                 parse_dates =  True,index_col = 0,header= None, sep =',',
                 names = ['meteo', 'empty'])
	return df

#Stats - Daily Month Annual
def basic_stats():
	file_name = db.sensors[request.args(0,cast=int)].myfile
	meteo_var = db.sensors[request.args(0,cast=int)].sensor_type
	station_name = db.sensors[request.args(0,cast=int)].station
	file_path  = os.path.join(request.folder,'uploads',file_name)
	time_span  = db.sensors[request.args(0,cast=int)].time_span
	df = pd.read_csv(file_path, skiprows = [num for (num,line) in enumerate(open(file_path),2) if 'Precision=' in line][0],
                 parse_dates =  True,index_col = 0,header= None, sep =',',
                 names = ['meteo', 'empty'])
	hows ="mean" #default how to aggregate
	form = ''
	if meteo_var in ['Rainfall','Snow']:
		hows = "sum"
	if meteo_var in ['Temperature','Discharge','Wind']:
		hows = "mean"
	if meteo_var in ['other']:
		form = SQLFORM.factory(
		Field('hows',requires = IS_IN_SET(["mean","sum"]))
		).process()
		if form.accepted:
			hows  = form.vars.hows

	# Statistics File Time Span - Monthly - Annual
	raw_stats= dict(df.meteo.resample('d',how = hows).describe())
	month_stats = dict(df.meteo.resample('M',how = hows).describe())
	annual_stats = dict(df.meteo.resample('A',how = hows).describe())

	#Plots
	day = df.meteo.resample('d',how = hows)
	plot_daily = plot3_bar(day.index,day,"",'',meteo_var)
	#plot_raw = plot3(df.meteo,"Raw Dataset",time_span,meteo_var)
	#Month
	month = df.meteo.resample('M',how = hows)
	subplot(2,1,1)
	plot_month = plot3_bar(month.index,month,"",'',meteo_var)
	#Annual
	annual = df.meteo.resample('A',how = hows)
	subplot(2,2,1)
	plot_annual = plot3_bar(annual.index,annual,"",'',meteo_var)
	return dict(raw_stats=raw_stats,month_stats=month_stats,annual_stats=annual_stats,station_name=station_name,\
		meteo_var=meteo_var,time_span=time_span,plot_daily = plot_daily,plot_month =plot_month,\
		plot_annual = plot_annual)

#Over Thershold 
def over_threshold():
	file_name = db.sensors[request.args(0,cast=int)].myfile
	meteo_var = db.sensors[request.args(0,cast=int)].sensor_type
	station_name = db.sensors[request.args(0,cast=int)].station
	file_path  = os.path.join(request.folder,'uploads',file_name)
	time_span  = db.sensors[request.args(0,cast=int)].time_span
	df = pd.read_csv(file_path, skiprows = [num for (num,line) in enumerate(open(file_path),2) if 'Precision=' in line][0],
                 parse_dates =  True,index_col = 0,header= None, sep =',',
                 names = ['meteo', 'empty'])

	max_value = df.meteo.max()
	min_value = df.meteo.min()
	#Select Threshold
	form = SQLFORM.factory(
		Field('threshold', 'double', default =0.1)).process()
	over_threshold = ''
	plot_hist_threshold = ''
	plot_threshold = ''
	if form.vars.threshold>max_value or form.vars.threshold<min_value:
		response.flash = "You must enter values between Min - Max Variable Value"

	if form.accepted:
		over_threshold = dict(df[df.meteo >= form.vars.threshold].meteo.describe())
		data = df[df.meteo >= form.vars.threshold].meteo
		plot_threshold = plot3_bar(data.index,data,"Over Threshold Dataset",time_span,meteo_var)
		plot_hist_threshold = hist_cum3_plot(data)
	return dict(form=form, max_value=max_value, min_value=min_value,\
		plot_threshold = plot_threshold,plot_hist_threshold = plot_hist_threshold,\
		station_name = station_name,meteo_var = meteo_var,over_threshold = over_threshold)

#Plot one 
def plot3(data_index,data,title,xlabel,ylabel):
	import mpld3
	fig, ax = plt.subplots(figsize=(12, 4),sharey=True, sharex=True)
	ax.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
	ax.plot(data_index,data)
	ax.set_title(title)
	ax.set_xlabel(xlabel)
	ax.set_ylabel(ylabel)
	make_html = mpld3.fig_to_html(fig, template_type = "general")
	return make_html

#Plot Bar 
def plot3_bar(data_index,data,title,xlabel,ylabel):
	import mpld3
	fig, ax = plt.subplots(figsize=(12, 4),sharey=True, sharex=True)
	ax.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
	ax.bar(data_index,data)
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

#Events 
def events():
	sensor_id = request.args(0,cast=int)
	file_name = db.sensors[request.args(0,cast=int)].myfile
	meteo_var = db.sensors[request.args(0,cast=int)].sensor_type
	station_name = db.sensors[request.args(0,cast=int)].station
	file_path  = os.path.join(request.folder,'uploads',file_name)
	time_span  = db.sensors[request.args(0,cast=int)].time_span
	df = pd.read_csv(file_path, skiprows = [num for (num,line) in enumerate(open(file_path),2) if 'Precision=' in line][0],
                 parse_dates =  True,index_col = 0,header= None, sep =',',
                 names = ['meteo', 'empty'])
	df['date'] = df.index 
	df = df.drop(['empty'], axis=1)
	max_value = df.meteo.max()
	min_value = df.meteo.min()
	a = 1
	df1=''
	form = SQLFORM.factory(
		Field('threshold', 'double', default =0.1),
		Field('timespam','int',default = 120,comment= "In minutes",label = "TimeSpam Between Events"),
		Field('sort_by', default = "sum",requires = IS_IN_SET(['mean','min','max','sum']))).process(keepvalues = True)
	if form.accepted:
		a = 2
		df = df[df.meteo >  form.vars.threshold]
		diff = df.date - df.date.shift(1)
		df['event_id'] = (diff > np.timedelta64(form.vars.timespam, "m")).astype(int).cumsum()
		start     = [row for row in df.date.groupby(df.event_id).min()]
		finish    = [row for row in df.date.groupby(df.event_id).max()]
		mean      = [row for row in df.meteo.groupby(df.event_id).mean()]
		sum       = [ row for row in df.meteo.groupby(df.event_id).sum()]
		min       = [row for row in df.meteo.groupby(df.event_id).min()]
		max       = [row for row in df.meteo.groupby(df.event_id).max()]
		event_id  = [row for row in df.event_id.groupby(df.event_id).max()]
		d = {'start':start, 'finish':finish,'mean' :mean,'min':min,'max':max,'sum':sum}
		df1 = pd.DataFrame(d)
		df1['duration'] = df1.finish-df1.start
		df1  = df1.sort([form.vars.sort_by],ascending = False)
	return dict(station_name = station_name,meteo_var=meteo_var,form=form,a=a,df1=df1,\
		sensor_id=sensor_id,df=df)




















#############