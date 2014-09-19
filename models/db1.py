
##waterdrop table 
db.define_table('waterdrop',
	Field('name','string', label = "Title"),
	Field('notes','text',label = "Notes", default="Add Basic Notes"),
	auth.signature,
	format = '%(name)s'
	)
db.waterdrop.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db,db.waterdrop.name)]

### comment on waterdrop
db.define_table('comment_post',
	Field('name','reference waterdrop'),
	Field('body','string',label = "Comments", default = "add your comment here"),
   	auth.signature,
   	format ='%(body)s')

##basin table
db.define_table('basins',
	Field('waterdrop','reference waterdrop'),
	Field('name','string',default ="add Basin name"),
	Field('basin_type',requires = IS_IN_SET(["Main","Sub"]),default = "Main"),
	Field('hmax','double',default = 100, comment = "m"),
	Field('hmin','double',default = 20, comment = "m"),
	Field('river_name','string', default = "Add your own river name"),
	Field('area','double',default = 20, comment = "km2"),
	Field('perimeter','double',default = 20, comment = "m"),
	Field('river_lenght','double',label ="Main River Lenght", default = 10,comment = "km"),
	Field('lat','double',label="Basin Center Lat", default = 37.0,comment = "WGS84 Decimal Degrees"),
	Field('lon','double',label ="Basin Center Lon",default = 22.0,comment = "WGS84 Decimal Degrees"),
	auth.signature,
	format = '%(name)s')
db.basins.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db,db.basins.name)]

##station table 
db.define_table('stations',
	Field('name','string',default ="add Station Name"),
	Field('waterdrop','reference waterdrop'),
	Field('station_type',requires = IS_IN_SET(['Meteorological','Stage - Hydrometric', 'Both','Something Else...'])),
	Field('status', requires = IS_IN_SET(['Still Recording', 'Not Active', 'I dont Know...'])),
	Field('alt','double', default = 100, comment = "m"),
	Field('lat','double',label="Lat",default = 37.0,comment = "WGS84 Decimal Degrees"),
	Field('lon','double',label = "Lon",default = 22.23,comment = "WGS84 Decimal Degrees"),
	auth.signature,
	auth.signature,
	format ='%(name)s')
db.stations.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db,db.stations.name)]

#sensors table
meteo_vars = ["Rainfall", "Snow","Temperature","Discharge","Wind","other"]
time_span  = ["10 mins","15 mins","30 mins","Hourly","Daily","Weekly","Monthly","Annual"]


db.define_table('sensors',
	Field('station','reference stations'),
	Field('waterdrop','reference waterdrop'),
	Field('sensor_type', requires = IS_IN_SET(meteo_vars)),
	Field('time_span', requires = IS_IN_SET(time_span)),
	Field("myfile", "upload",requires = IS_NOT_EMPTY()),
	auth.signature)


















