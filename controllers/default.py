# -*- coding: utf-8 -*-
import folium
import os

def index():
#Row Basins
    basins = db((db.basins.id>0) & (db.basins.created_by != 2)).select(db.basins.lat,db.basins.lon,db.basins.name)
    #Map 
    zoom_starts = 5
    default_center = [35,35]
    map_1 = folium.Map(location= default_center, zoom_start= zoom_starts,tiles='OpenStreetMap')
    ##for loop for basins points
    for item in basins:
        map_1.circle_marker(location =[item.lat,item.lon], popup= "Basin Name: "  + str(item.name), radius=500,
                      popup_on=True, line_color='black',
                    fill_color='red')
    ##for loop for stations points
    stations_coords = db((db.stations.id>0) & (db.stations.created_by != 2)).select(db.stations.lat,db.stations.lon,db.stations.name)
    for item in stations_coords:
        map_1.circle_marker(location =[item.lat,item.lon], popup= "Station Name: "  + str(item.name), radius=500,
                      popup_on=True, line_color='black',
                    fill_color='#3186cc')

    path = os.path.join(request.folder,'static','currentdb_map.html')
    map_1.create_map(path=path)

    #Count Waterdrops Stuff
    num_waterdrops = db((db.waterdrop.id>0) & (db.waterdrop.created_by != 2)).count()
    num_basins = db((db.basins.id>0) & (db.basins.created_by != 2)).count()
    num_stations = db((db.stations.id>0) & (db.stations.created_by != 2)).count()
    num_sensors  = db((db.sensors.id>0) & (db.sensors.created_by !=2)).count()
    
    #Quick Selection 
    form = SQLFORM.factory(
        Field("waterdrop",label="Quick Selection", requires = IS_IN_DB(db,db.waterdrop.name)),formstyle=bs3.form()).process()
    #form process()
    if form.accepted:
        waterdrop_id = db(db.waterdrop.name == form.vars.waterdrop).select(db.waterdrop.id).first()['id']
        redirect(URL('profile','index', args = waterdrop_id))
    return dict(path = path, form = form, num_sensors = num_sensors, num_stations = num_stations,num_basins=num_basins,num_waterdrops=num_waterdrops)


def select():
    map = index_map()
    waterdrops = db(db.waterdrop.id>0).select(orderby=~db.waterdrop.created_on)
    return locals()

@auth.requires_login()
def create():
#Created a waterdrop (Field name and notes)
    db.waterdrop.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db,db.waterdrop.name)]
    db.waterdrop.name.label    = "Add Waterdrop Title"
    db.waterdrop.notes.label   = "Add Basic Notes"
    form = SQLFORM(db.waterdrop,formstyle=bs3.form()).process()

    if form.accepted:
        redirect(URL('profile','index', args = form.vars.id))
    elif form.errors:
        response.flash = "..Check entered values"
    else:
        pass
    return dict(form=form)

def about():
    message = "Hello from about"
    return locals()

def help():
    message = "Documents"
    return locals()

def index_map():
    basins = db(db.basins.id>0).select(db.basins.lat,db.basins.lon,db.basins.name)
    #Map 
    zoom_starts = 4
    default_center = [28,55]
    map_1 = folium.Map(location= default_center, zoom_start= zoom_starts,tiles='OpenStreetMap')
    ##for loop for basins points
    for item in basins:
        map_1.circle_marker(location =[item.lat,item.lon], popup= "Basin Name: "  + str(item.name), radius=500,
                      popup_on=True, line_color='black',
                    fill_color='red')
    ##for loop for stations points
    stations_coords = db(db.stations.id>0).select(db.stations.lat,db.stations.lon,db.stations.name)
    for item in stations_coords:
        map_1.circle_marker(location =[item.lat,item.lon], popup= "Station Name: "  + str(item.name), radius=500,
                      popup_on=True, line_color='black',
                    fill_color='#3186cc')

    path = os.path.join(request.folder,'static','currentdb_map.html')
    map_1.create_map(path=path)

    #Count Stuff
    num_waterdrops = db(db.waterdrop.id>0).count()
    num_basins = db(db.basins.id>0).count()
    num_stations = db(db.stations.id>0).count()
    num_sensors  = db(db.sensors.id>0).count()
    return locals()

def further_steps():

    return locals()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
