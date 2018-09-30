from flask import Flask, render_template
import geojson
from math import pow, sqrt, pi
from requests import get

app = Flask(__name__)
app.config.from_object(__name__)

# Get Mapbox access token
app.config.from_envvar('APP_CONFIG_FILE', silent=True)
MAPBOX_ACCESS_KEY = app.config['MAPBOX_ACCESS_KEY']

def get_earthquake_data():
    """
    Fetching the earthquakes of the last 30 days from the usgs API.
    Returns a geojson object.
    """
    _format = 'geojson'
    resp = get('https://earthquake.usgs.gov/fdsnws/event/1/query?format={}'.format(_format))
    if resp.status_code == 200:
        earthquakes = geojson.loads(resp.content)
        return earthquakes['features']
    
def get_tectonic_plate_data():
    """
    Loading geospatial data of earth's tectonic plates. Returns a geojson object.
    Source: https://github.com/fraxen/tectonicplates 

    TODO: Include the license in the .md file: https://opendatacommons.org/licenses/by/1.0/. See what Fraxen did. 
    Credits to Hugo Ahlenius, Nordpil and Peter Bird for the data source.
    The data was obtained form
    Original source data: http://peterbird.name/oldFTP/PB2002/
    Converted to geojson format by 
    https://github.com/fraxen/tectonicplates 
    """
    with open('tectonic_plates.geojson.json', 'r') as infile:
        plates = geojson.load(infile)
        return plates

def get_circle_radius(mag):
    return sqrt(pow(10, mag) / pi)

def remap(value_old, min_old, max_old, min_new, max_new):
    range_old = (max_old - min_old)
    range_new = (max_new - min_new)
    value_new = (((value_old - min_old) * range_new) / range_old) + min_new
    return value_new

def prepare_geojson(earthquake):   
    """
    Prepare the geojson data of the earthquakes by creating a new geojson object 
    that only contains the parameters required for the map in order to increase
    performance. 

    Calculates and remaps the circle-radius based on a earthquake's magnitude.
    Returns a geojson format with long, lat, mag, radius parameters.
    """
    
    feature_list = []
    mag_max = sqrt(pow(10, 10))

    for earthquake in earthquakes:
        point = geojson.Point(earthquake['geometry']['coordinates'][:2])
        
        properties = {}
        mag = earthquake['properties']['mag']
        if mag is None:
            continue
        properties['mag'] = mag
        circle_radius = get_circle_radius(mag)
        properties['radius'] = remap(circle_radius, 0, mag_max, 2, 1500)
        feature = geojson.Feature(geometry=point, properties=properties)        
        feature_list.append(feature)

    return geojson.FeatureCollection(feature_list)


# TODO: move both in earthquake_vizualiation() and solve global variable problem
earthquakes = get_earthquake_data()
plates = get_tectonic_plate_data()

earthquakes = prepare_geojson(earthquakes)

@app.route('/earthquakes')
def earthquakes_visualization():
    return render_template(
        'mapbox_gl.html', 
        ACCESS_KEY=MAPBOX_ACCESS_KEY,
        earthquakes = earthquakes,
        plates = plates
    )