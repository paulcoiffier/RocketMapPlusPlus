import math
import geopy
import geopy.distance
import random

a = 6378245.0
ee = 0.00669342162296594323
pi = 3.14159265358979324

macau_border = [
    {"latitude": 22.207514407609402, "longitude": 113.53480603903813},
    {"latitude": 22.209351997243783, "longitude": 113.53425886839909},
    {"latitude": 22.21060875777704, "longitude": 113.5337265676701},
    {"latitude": 22.21135371302128, "longitude": 113.53339397375225},
    {"latitude": 22.212098664310567, "longitude": 113.53331887189984},
    {"latitude": 22.213141589471075, "longitude": 113.53472434942364},
    {"latitude": 22.213449499226712, "longitude": 113.5361405557835},
    {"latitude": 22.213383261719574, "longitude": 113.53829705183148},
    {"latitude": 22.2129263629142, "longitude": 113.54026042883038},
    {"latitude": 22.213055486640464, "longitude": 113.54189121191143},
    {"latitude": 22.21560813898635, "longitude": 113.54308123906958},
    {"latitude": 22.21640272945934, "longitude": 113.54358549436438},
    {"latitude": 22.21681988765599, "longitude": 113.54432578405249},
    {"latitude": 22.216849684622577, "longitude": 113.54518409093725},
    {"latitude": 22.216680835061613, "longitude": 113.54548449834692},
    {"latitude": 22.216656978296218, "longitude": 113.5471753163331},
    {"latitude": 22.216537790228198, "longitude": 113.54754009675912},
    {"latitude": 22.216656978296218, "longitude": 113.54820528459481},
    {"latitude": 22.21657901729732, "longitude": 113.5489170513548},
    {"latitude": 22.216611297399588, "longitude": 113.54927378515379},
    {"latitude": 22.21674786698083, "longitude": 113.54974048952238},
    {"latitude": 22.21690678414438, "longitude": 113.54998725275175},
    {"latitude": 22.21694154724991, "longitude": 113.55024206260816},
    {"latitude": 22.21702100574448, "longitude": 113.55078386882917},
    {"latitude": 22.21564299036599, "longitude": 113.55077187459631},
    {"latitude": 22.21549696007803, "longitude": 113.55141764965879},
    {"latitude": 22.215084764170633, "longitude": 113.55237251606809},
    {"latitude": 22.214235079151624, "longitude": 113.5543115615817},
    {"latitude": 22.213445442682694, "longitude": 113.55604963302335},
    {"latitude": 22.213151345943242, "longitude": 113.55689779752106},
    {"latitude": 22.21314637965167, "longitude": 113.55715528958649},
    {"latitude": 22.212483332334276, "longitude": 113.5588128947577},
    {"latitude": 22.21132120978135, "longitude": 113.56099084847779},
    {"latitude": 22.204368138769, "longitude": 113.56292203896851},
    {"latitude": 22.187957525723302, "longitude": 113.56644109719605},
    {"latitude": 22.168220091638695, "longitude": 113.5667127730078},
    {"latitude": 22.1731481425775, "longitude": 113.5751241804785},
    {"latitude": 22.169491863254862, "longitude": 113.58782712237303},
    {"latitude": 22.134288954990772, "longitude": 113.60143626399645},
    {"latitude": 22.10900401690852, "longitude": 113.5683056182445},
    {"latitude": 22.109737582217022, "longitude": 113.55334650015789},
    {"latitude": 22.111407473453415, "longitude": 113.550664291143},
    {"latitude": 22.113037586301715, "longitude": 113.54935537314373},
    {"latitude": 22.115831539461425, "longitude": 113.54933611322633},
    {"latitude": 22.118614560256564, "longitude": 113.54972235132448},
    {"latitude": 22.121411611091922, "longitude": 113.5495292322754},
    {"latitude": 22.125162760379855, "longitude": 113.55068794656984},
    {"latitude": 22.128601543265393, "longitude": 113.55058065820924},
    {"latitude": 22.13799165675807, "longitude": 113.5512029307007},
    {"latitude": 22.146204498846757, "longitude": 113.54965797830812},
    {"latitude": 22.149752715540536, "longitude": 113.54734085520181},
    {"latitude": 22.152932540417268, "longitude": 113.54356430490884},
    {"latitude": 22.156509757522947, "longitude": 113.54030273874673},
    {"latitude": 22.166175861752283, "longitude": 113.53710118732579},
    {"latitude": 22.177065192092236, "longitude": 113.53177968464024},
    {"latitude": 22.18477464586574, "longitude": 113.52765981159337},
    {"latitude": 22.187086485934902, "longitude": 113.52939717673985},
    {"latitude": 22.189907834906375, "longitude": 113.53111379050938},
    {"latitude": 22.192694283789987, "longitude": 113.53362433814732},
    {"latitude": 22.195773799491587, "longitude": 113.5351692905399},
    {"latitude": 22.20097902086778, "longitude": 113.53598468208043},
    {"latitude": 22.20725681738251, "longitude": 113.53493325614659}
]


def transform_from_wgs_to_gcj(latitude, longitude):
    if is_location_out_of_china(latitude, longitude) or is_location_in_macau(latitude, longitude):
        adjust_lat, adjust_lon = latitude, longitude
    else:
        adjust_lat = transform_lat(longitude - 105, latitude - 35.0)
        adjust_lon = transform_long(longitude - 105, latitude - 35.0)
        rad_lat = latitude / 180.0 * pi
        magic = math.sin(rad_lat)
        magic = 1 - ee * magic * magic
        math.sqrt_magic = math.sqrt(magic)
        adjust_lat = (adjust_lat *
                      180.0) / ((a * (1 - ee)) / (magic *
                                                  math.sqrt_magic) * pi)
        adjust_lon = (adjust_lon *
                      180.0) / (a / math.sqrt_magic * math.cos(rad_lat) * pi)
        adjust_lat += latitude
        adjust_lon += longitude
    #  Print 'transfromed from ', wgs_loc, ' to ', adjust_loc.
    return adjust_lat, adjust_lon


def is_location_in_macau(latitude, longitude):
    inside = False
    sides = len(macau_border)
    j = sides - 1

    for i, item in enumerate(macau_border):
        if (
            (
                (
                    (macau_border[i]['longitude'] <= longitude) and (longitude < macau_border[j]['longitude'])
                ) or (
                    (macau_border[j]['longitude'] <= longitude) and (longitude < macau_border[i]['longitude'])
                )
            ) and
            (latitude < (macau_border[j]['latitude'] - macau_border[i]['latitude']) * (
                longitude - macau_border[i]['longitude']) / (
                 macau_border[j]['longitude'] - macau_border[i]['longitude']) + macau_border[i]['latitude'])
        ):
            inside = not inside

        j = i
    return inside


def is_location_out_of_china(latitude, longitude):
    if (longitude < 72.004 or longitude > 137.8347 or
            latitude < 0.8293 or latitude > 55.8271):
        return True
    return False


def transform_lat(x, y):
    lat = (-100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y +
           0.1 * x * y + 0.2 * math.sqrt(abs(x)))
    lat += (20.0 * math.sin(6.0 * x * pi) + 20.0 *
            math.sin(2.0 * x * pi)) * 2.0 / 3.0
    lat += (20.0 * math.sin(y * pi) + 40.0 *
            math.sin(y / 3.0 * pi)) * 2.0 / 3.0
    lat += (160.0 * math.sin(y / 12.0 * pi) + 320 *
            math.sin(y * pi / 30.0)) * 2.0 / 3.0
    return lat


def transform_long(x, y):
    lon = (300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y +
           0.1 * math.sqrt(abs(x)))
    lon += (20.0 * math.sin(6.0 * x * pi) + 20.0 *
            math.sin(2.0 * x * pi)) * 2.0 / 3.0
    lon += (20.0 * math.sin(x * pi) + 40.0 *
            math.sin(x / 3.0 * pi)) * 2.0 / 3.0
    lon += (150.0 * math.sin(x / 12.0 * pi) + 300.0 *
            math.sin(x / 30.0 * pi)) * 2.0 / 3.0
    return lon


# Returns destination coords given origin coords, distance (Kms) and bearing.
def get_new_coords(init_loc, distance, bearing):
    """
    Given an initial lat/lng, a distance(in kms), and a bearing (degrees),
    this will calculate the resulting lat/lng coordinates.
    """
    origin = geopy.Point(init_loc[0], init_loc[1])
    destination = geopy.distance.distance(kilometers=distance).destination(
        origin, bearing)
    return (destination.latitude, destination.longitude)


# Returns destination coords given origin coords, distance (Ms) and bearing.
# This version is less precise and almost 1 order of magnitude faster than
# using geopy.
def fast_get_new_coords(origin, distance, bearing):
    R = 6371009  # IUGG mean earth radius in kilometers.

    oLat = math.radians(origin[0])
    oLon = math.radians(origin[1])
    b = math.radians(bearing)

    Lat = math.asin(
        math.sin(oLat) * math.cos(distance / R) +
        math.cos(oLat) * math.sin(distance / R) * math.cos(b))

    Lon = oLon + math.atan2(
        math.sin(bearing) * math.sin(distance / R) * math.cos(oLat),
        math.cos(distance / R) - math.sin(oLat) * math.sin(Lat))

    return math.degrees(Lat), math.degrees(Lon)


# Apply a location jitter.
def jitter_location(location=None, max_meters=5):
    origin = geopy.Point(location[0], location[1])
    bearing = random.randint(0, 360)
    distance = math.sqrt(random.random()) * (float(max_meters))
    destination = fast_get_new_coords(origin, distance, bearing)
    return (destination[0], destination[1], location[2])


# Computes the intermediate point at any fraction along the great circle path.
def intermediate_point(pos1, pos2, fraction):
    if pos1 == pos2:
        return pos1

    lat1 = math.radians(pos1[0])
    lon1 = math.radians(pos1[1])
    lat2 = math.radians(pos2[0])
    lon2 = math.radians(pos2[1])

    # Spherical Law of Cosines.
    slc = (math.sin(lat1) * math.sin(lat2) +
           math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))

    if slc > 1:
        # Locations are too close to each other.
        return pos1 if fraction < 0.5 else pos2

    delta = math.acos(slc)

    if delta == 0:
        # Locations are too close to each other.
        return pos1 if fraction < 0.5 else pos2

    # Intermediate point.
    a = math.sin((1 - fraction) * delta) / delta
    b = math.sin(fraction * delta) / delta
    x = (a * math.cos(lat1) * math.cos(lon1) +
         b * math.cos(lat2) * math.cos(lon2))
    y = (a * math.cos(lat1) * math.sin(lon1) +
         b * math.cos(lat2) * math.sin(lon2))
    z = a * math.sin(lat1) + b * math.sin(lat2)

    lat3 = math.atan2(z, math.sqrt(x**2 + y**2))
    lon3 = math.atan2(y, x)

    return (((math.degrees(lat3) + 540) % 360) - 180,
            ((math.degrees(lon3) + 540) % 360) - 180)
