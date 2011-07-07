from urllib2 import urlopen
import simplejson

from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.translation import get_language

from molly.utils.templatetags.molly_utils import humanise_seconds

CLOUDMADE_URL = 'http://routes.cloudmade.com/%s/api/0.3/' % settings.API_KEYS['cloudmade']

def generate_route(points, type):
    """
    Given 2 Points, this will return a route between them. The route consists
    of a dictionary with the following keys:
    
    * error (optional, and if set means that the object contains no route),
      which is a string describing any errors that occurred in plotting the
      route
    * total_time: An int of the number of seconds this route is estimated to
      take
    * total_distance: An int of the number of metres this route is expected to
      take
    * waypoints: A list of dictionaries, where each dictionary has 2 keys:
      'instruction', which is a human-readable description of the steps to be
      taken here, and 'location', which is a Point describing the route to be
      taken
    
    @param points: An ordered list of points to be included in this route
    @type points: [Point]
    @param type: The type of route to generate (foot, car or bike)
    @type type: str
    @return: A dictionary containing the route and metadata associated with it
    @rtype: dict
    """
    
    # Build cloudmade request:
    points = map(lambda p: ','.join(reversed(map(str, p))), points)
    url = CLOUDMADE_URL + ','.join(points) + '/%s.js?lang=%s' % (type, get_language()[:2])
    
    json = simplejson.load(urlopen(url))
    
    if json['status'] != 0:
        return {
            'error': json['status_message']
        }
    else:
        
        points = [Point(p[1], p[0], srid=4326) for p in json['route_geometry']]
        waypoints = []
        for i, waypoint in enumerate(json['route_instructions']):
            if i == 0:
                (instruction, length, position, time, length_caption,
                 earth_direction, azimuth) = waypoint
            else:
                (instruction, length, position, time, length_caption,
                 earth_direction, azimuth, turn_type, turn_angle) = waypoint
            waypoints.append({
                'instruction': '%s, heading %s for %s (taking approximately %s)' % (
                    instruction, earth_direction, length_caption,
                    humanise_seconds(time)),
                'location': points[position]
            })
        
        return {
            'total_time': json['route_summary']['total_time'],
            'total_distance': json['route_summary']['total_distance'],
            'waypoints': waypoints
        }