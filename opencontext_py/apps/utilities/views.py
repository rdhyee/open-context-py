import json
import random
from django.http import HttpResponse, Http404
from django.conf import settings
from django.template import RequestContext, loader
from opencontext_py.libs.rootpath import RootPath
from opencontext_py.libs.requestnegotiation import RequestNegotiation
from opencontext_py.libs.general import LastUpdatedOrderedDict
from opencontext_py.libs.globalmaptiles import GlobalMercator
from opencontext_py.apps.imports.fields.datatypeclass import DescriptionDataType
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache


@cache_control(no_cache=True)
@never_cache
def human_remains_ok(request):
    """ toggles if the user opts-in or opts-out
        to view human remains
        for this user's session
    """
    prev_opt_in = request.session.get('human_remains_ok')
    if prev_opt_in:
        request.session['human_remains_ok'] = False
    else:
        request.session['human_remains_ok'] = True
    output = LastUpdatedOrderedDict()
    output['previous_opt_in'] = prev_opt_in
    output['new_opt_in'] = request.session['human_remains_ok']
    return HttpResponse(json.dumps(output,
                                   ensure_ascii=False,
                                   indent=4),
                        content_type='application/json; charset=utf8')

def meters_to_lat_lon(request):
    """ Converts Web mercator meters to WGS-84 lat / lon """
    gm = GlobalMercator()
    mx = None
    my = None
    if request.GET.get('mx') is not None:
        mx = request.GET['mx']
    if request.GET.get('my') is not None:
        my = request.GET['my']
    try:
        mx = float(mx)
    except:
        mx = False
    try:
        my = float(my)
    except:
        my = False
    if isinstance(mx, float) and isinstance(my, float):
        lat_lon = gm.MetersToLatLon(mx, my)
        output = LastUpdatedOrderedDict()
        if len(lat_lon) > 0:
            output['lat'] = lat_lon[0]
            output['lon'] = lat_lon[1]
        else:
            output['error'] = 'Stange error, invalid numbers?'
        return HttpResponse(json.dumps(output,
                                       ensure_ascii=False,
                                       indent=4),
                            content_type='application/json; charset=utf8')
    else:
        return HttpResponse('mx and my paramaters must be numbers',
                            status=406)
    

def lat_lon_to_quadtree(request):
    """ Converts WGS-84 lat / lon to a quadtree tile of a given zoom level """
    gm = GlobalMercator()
    lat = None 
    lon = None
    rand = None
    lat_ok = False
    lon_ok = False
    zoom = gm.MAX_ZOOM
    if request.GET.get('lat') is not None:
        lat = request.GET['lat']
        lat_ok = gm.validate_geo_coordinate(lat, 'lat')
    if request.GET.get('lon') is not None:
        lon = request.GET['lon']
        lon_ok = gm.validate_geo_coordinate(lon, 'lon')
    if request.GET.get('zoom') is not None:
        check_zoom = request.GET['zoom']
        dtc_obj = DescriptionDataType()
        zoom = dtc_obj.validate_integer(check_zoom)
        if zoom is not None:
            # zoom is valid
            if zoom > gm.MAX_ZOOM:
                zoom = gm.MAX_ZOOM
            elif zoom < 1:
                zoom = 1
    if request.GET.get('rand') is not None:
        dtc_obj = DescriptionDataType()
        rand = dtc_obj.validate_numeric(request.GET['rand'])
    if lat_ok and lon_ok and zoom is not None:
        output = gm.lat_lon_to_quadtree(lat, lon, zoom)
        return HttpResponse(output,
                            content_type='text/plain; charset=utf8')
    else:
        message = 'ERROR: "lat" and "lon" parameters must be valid WGS-84 decimal degrees'
        if zoom is None:
            message += ', "zoom" parameter needs to be an integer between 1 and ' + str(gm.MAX_ZOOM) + '.'
        return HttpResponse(message,
                            content_type='text/plain; charset=utf8',
                            status=406)


def quadtree_to_lat_lon(request):
    """ Converts a quadtree tile to WGS-84 lat / lon coordinates in different formats """
    lat_lon = None
    gm = GlobalMercator()
    if request.GET.get('tile') is not None:
        tile = request.GET['tile']
        try:
            lat_lon = gm.quadtree_to_lat_lon(tile)
        except:
            lat_lon = None
    if lat_lon is not None:
        # default to json format with lat, lon dictionary object
        lat_lon_dict = LastUpdatedOrderedDict()
        lat_lon_dict['lat'] = lat_lon[0]
        lat_lon_dict['lon'] = lat_lon[1]
        output = json.dumps(lat_lon_dict,
                            ensure_ascii=False,
                            indent=4)
        content_type='application/json; charset=utf8'
        if request.GET.get('format') is not None:
            # client requested another format, give it if recognized
            if request.GET['format'] == 'geojson':
                # geojson format, with longitude then latitude
                output = json.dumps(([lat_lon[1], lat_lon[0]]),
                                    ensure_ascii=False,
                                    indent=4)
                content_type='application/json; charset=utf8'
            elif request.GET['format'] == 'lat,lon':
                # text format, with lat, comma lon coordinates
                output = str(lat_lon[0]) + ',' + str(lat_lon[1])
                content_type='text/plain; charset=utf8'
        return HttpResponse(output,
                            content_type=content_type)
    else:
        message = 'ERROR: "tile" must be a valid quadtree geospatial tile (string composed of digits ranging from 0-3)'
        return HttpResponse(message,
                            content_type='text/plain; charset=utf8',
                            status=406)