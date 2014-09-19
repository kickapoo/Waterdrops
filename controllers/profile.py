import folium
import os
import numpy as np

# Profile
def index():
	#Select waterdrop[id]
	waterdrop = db.waterdrop[request.args(0,cast =int)]
	#Map waterdrop
	default_center = map_profile(request.args(0,cast=int))
	#Waterdrop General Counts
	num_basins = db(db.basins.waterdrop == waterdrop.id).count()
	num_stations = db(db.stations.waterdrop == waterdrop.id).count()
	num_sensors  = db(db.sensors.waterdrop == waterdrop.id).count()
	#Comments Form
	db.comment_post.name.default = request.args(0,cast =int)
	db.comment_post.name.writable = db.comment_post.name.readable = False
	form  = SQLFORM(db.comment_post,formstyle=bs3.form('inline')).process()
	comments=db(db.comment_post.name == request.args(0,cast=int)).select(orderby=~db.comment_post.id,limitby=(0,2))
	#Count Catchment Section
	basins = db(db.basins.waterdrop == request.args(0,cast=int)).select()
	count_basins_totals = db(db.basins.waterdrop == request.args(0,cast=int)).count()
	count_basins_mains  = db((db.basins.waterdrop == request.args(0,cast=int)) \
		& (db.basins.basin_type == "Main")).count()
	count_basins_subs   = db((db.basins.waterdrop == request.args(0,cast=int)) \
		& (db.basins.basin_type == "Sub")).count()

	#Count Timeseries Section
	stations = db(db.stations.waterdrop == request.args(0,cast=int)).select()
	count_stations_totals = db(db.stations.waterdrop == request.args(0,cast=int)).count()
	count_sensors_totals = db(db.sensors.waterdrop == request.args(0,cast=int)).count()
	meteo_vars = meteo_vars = ["Rainfall", "Snow","Temperature","Discharge","Wind","other"]
	count_vars = []
	for meteo_var in meteo_vars:
		count_vars.append(db((db.sensors.waterdrop == request.args(0,cast=int)) \
		& (db.sensors.sensor_type == meteo_var)).count())

	#Add Catchment form
	db.basins.waterdrop.default = request.args(0,cast=int)
	db.basins.waterdrop.requires = db.basins.waterdrop.readable = db.basins.waterdrop.writable = False
	db.basins.area.requires = db.basins.area.readable = db.basins.area.writable = False
	db.basins.river_name.requires = db.basins.river_name.readable = db.basins.river_name.writable = False
	db.basins.perimeter.requires = db.basins.perimeter.readable = db.basins.perimeter.writable = False
	db.basins.hmax.requires = db.basins.hmax.readable = db.basins.hmax.writable = False
	db.basins.hmin.requires = db.basins.hmin.readable = db.basins.hmin.writable = False
	db.basins.river_lenght.requires = db.basins.river_lenght.readable = db.basins.river_lenght.writable = False
	db.basins.lat.requires = db.basins.lat.readable = db.basins.lat.writable = False
	db.basins.lon.requires = db.basins.lon.readable = db.basins.lon.writable = False
	form_catchment = SQLFORM(db.basins,formstyle=bs3.form()).process()
	#form process()
	if form_catchment.accepted:
		redirect(URL('profile','index',args = request.args(0,cast=int)))


	#Add Station Form
	stations = db(db.stations.waterdrop == request.args(0,cast=int)).select()
	count_stations_totals = db(db.stations.waterdrop == request.args(0,cast=int)).count()
	db.stations.waterdrop.default = request.args(0,cast=int)
	db.stations.waterdrop.requires = db.stations.waterdrop.readable = db.stations.waterdrop.writable = False
	db.stations.lat.requires = db.stations.lat.readable = db.stations.lat.writable = False
	db.stations.lon.requires = db.stations.lon.readable = db.stations.lon.writable = False
	db.stations.alt.requires = db.stations.alt.readable = db.stations.alt.writable = False
	db.stations.station_type.default = "Meteorological"
	db.stations.status.default = "Still Recording"

	form_stations = SQLFORM(db.stations,formstyle=bs3.form()).process(keepvalues =True)
	if form_stations.accepted:
		redirect(URL('profile','index',args = request.args(0,cast=int)))



	return dict(waterdrop = waterdrop,num_basins=num_basins,num_stations=num_stations,num_sensors=num_sensors, \
		form=form,comments = comments, default_center = default_center['default_center'],\
		count_basins_totals=count_basins_totals,count_basins_subs =count_basins_subs,count_basins_mains=count_basins_mains,\
		count_stations_totals=count_stations_totals,count_sensors_totals=count_sensors_totals,count_vars=count_vars,\
		form_catchment = form_catchment,form_stations = form_stations,\
		basins =basins,stations=stations)

#Map display
def map_profile(waterdrop_id):
	basins = db(db.basins.waterdrop == waterdrop_id).select()
	if basins:
		index_lat = max([item.lat for item in basins]) 
		index_log = max([item.lon for item in basins]) 
		default_center = [index_lat,index_log]
		zoom_starts = 11
	else:
		zoom_starts = 5
		default_center = [40,35]
	map_1 = folium.Map(location= default_center, zoom_start= zoom_starts,tiles='OpenStreetMap')
	##for loop for basins points
	for item in basins:
		map_1.circle_marker(location =[item.lat,item.lon], popup= "Basin Name: "  + str(item.name), radius=500,
                      popup_on=True, line_color='black',
                    fill_color='red')
	##for loop for stations points
	stations_coords = db(db.stations.waterdrop == waterdrop_id).select(db.stations.lat,db.stations.lon,db.stations.name)
	for item in stations_coords:
		map_1.circle_marker(location =[item.lat,item.lon], popup= "Station Name: "  + str(item.name), radius=500,
                      popup_on=True, line_color='black',
                    fill_color='#3186cc')
	path = os.path.join(request.folder,'static','profile_map.html')
	map_1.create_map(path=path)
	return dict(default_center = default_center)


#Waterdrop Name Edit / delete
@auth.requires_login()
def profile_edit():
	db.waterdrop.notes.requires = db.waterdrop.notes.writable = db.waterdrop.notes.readable = False
	form = SQLFORM(db.waterdrop,request.args(0,cast=int),formstyle=bs3.form()).process()
	if form.accepted:
		redirect(URL('profile','index',args = request.args(0,cast=int)))	
	return dict(form=form)

@auth.requires_login()
def profile_delete():
	delete = db(db.waterdrop.id == request.args(0,cast=int)).delete()
	redirect(URL('default','select'))
	return locals()


#Notes
#Edit profile notes
@auth.requires_login()
def profile_edit_notes():
	db.waterdrop.name.requires = db.waterdrop.name.writable = db.waterdrop.name.readable = False
	form = SQLFORM(db.waterdrop	,request.args(0,cast=int), formstyle=bs3.form()).process()
	if form.accepted:
		redirect(URL('profile','index',args = request.args(0,cast=int)))	
	return dict(form=form)

#Comments
@auth.requires_login()
def profile_comments():
	default_center = map_profile(request.args(0,cast=int))
	db.comment_post.name.default = request.args(0,cast =int)
	db.comment_post.name.label   = "Waterdrop Title"
	db.comment_post.name.writable = False
	db.comment_post.body.label = "Add Comment"
	form=SQLFORM(db.comment_post,formstyle=bs3.form()).process()
	comments=db(db.comment_post.name == request.args(0,cast=int)).select(orderby=~db.comment_post.id)
	return dict(form=form, comments=comments,default_center = default_center['default_center'])


#Basin Section 
def view_basin():
	basin = db(db.basins.id == request.args(0,cast=int)).select()
	return dict(basin = basin)

def view_all_basins():
	#Map waterdrop
	default_center = map_profile(request.args(0,cast=int))
	basins = db(db.basins.waterdrop == request.args(0,cast=int)).select()
	return dict(basins = basins,default_center = default_center['default_center'])

@auth.requires_login()
def edit_basin():
	form = SQLFORM(db.basins,request.args(0,cast=int),formstyle=bs3.form()).process()
	return locals()

@auth.requires_login()
def delete_basin():
	waterdrop = db((db.basins.id == request.args(0,cast=int)) & (db.basins.waterdrop == db.waterdrop.id)).select().first()
	waterdrop_id = waterdrop.waterdrop.id
	delete = db(db.basins.id == request.args(0,cast=int)).delete()
	redirect(URL('profile','index', args = waterdrop_id))
	return locals()

#Station Section 
@auth.requires_login()
def delete_station():
	waterdrop = db((db.stations.id == request.args(0,cast=int)) & (db.stations.waterdrop == db.waterdrop.id)).select().first()
	waterdrop_id = waterdrop.waterdrop.id
	delete = db(db.stations.id == request.args(0,cast=int)).delete()
	redirect(URL('profile','index', args = waterdrop_id))
	return locals()

@auth.requires_login()
def edit_station():
	form = SQLFORM(db.stations,request.args(0,cast=int),formstyle=bs3.form()).process()
	return locals()

def view_station():
	default_center = map_profile(request.args(0,cast=int))
	station = db(db.stations.id == request.args(0,cast=int)).select()
	return dict(station=station,default_center = default_center['default_center'])

def view_all_stations():
	default_center = map_profile(request.args(0,cast=int))
	stations = db(db.stations.waterdrop == request.args(0,cast=int)).select()
	return dict(stations=stations,default_center = default_center['default_center'])


#Sensors Section
@auth.requires_login()
def add_sensor():
	db.sensors.station.default = request.args(0,cast=int)
	db.sensors.waterdrop.default = request.args(1,cast=int)
	form = SQLFORM(db.sensors).process(keepvalues =True)
	return locals()

@auth.requires_login()
def delete_sensor():
	delete = db(db.sensors.id == request.args(0,cast=int)).delete()
	redirect(URL('profile','view_all_sensors',args = request.args(1,cast=int)))
	return locals()

def view_all_sensors():
	sensors = db(db.sensors.waterdrop == request.args(0,cast=int)).select()
	return dict(sensors=sensors)

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)































	