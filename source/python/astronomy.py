#!/usr/bin/env python3

import math
import datetime

_PI2 = 2.0 * math.pi
_EPOCH = datetime.datetime(2000, 1, 1, 12)
_T0 = 2451545.0
_MJD_BASIS = 2400000.5
_Y2000_IN_MJD = _T0 - _MJD_BASIS
_DEG2RAD = 0.017453292519943296
_RAD2DEG = 57.295779513082321
_ASEC360 = 1296000.0
_ASEC2RAD = 4.848136811095359935899141e-6
_ARC = 3600.0 * 180.0 / math.pi     # arcseconds per radian
_C_AUDAY = 173.1446326846693        # speed of light in AU/day
_ERAD = 6378136.6                   # mean earth radius in meters
_AU = 1.4959787069098932e+11        # astronomical unit in meters
_KM_PER_AU = 1.4959787069098932e+8
_ANGVEL = 7.2921150e-5
_SECONDS_PER_DAY = 24.0 * 3600.0
_SOLAR_DAYS_PER_SIDEREAL_DAY = 0.9972695717592592
_MEAN_SYNODIC_MONTH = 29.530588
_EARTH_ORBITAL_PERIOD = 365.256
_REFRACTION_NEAR_HORIZON = 34.0 / 60.0
_SUN_RADIUS_AU  = 4.6505e-3
_MOON_RADIUS_AU = 1.15717e-5
_ASEC180 = 180.0 * 60.0 * 60.0

def _LongitudeOffset(diff):
    offset = diff
    while offset <= -180.0:
        offset += 360.0
    while offset > 180.0:
        offset -= 360.0
    return offset

def _NormalizeLongitude(lon):
    while lon < 0.0:
        lon += 360.0
    while lon >= 360.0:
        lon -= 360.0
    return lon

class Vector:
    def __init__(self, x, y, z, t):
        self.x = x
        self.y = y
        self.z = z
        self.t = t

    def Length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

BODY_INVALID = -1
BODY_MERCURY = 0
BODY_VENUS = 1
BODY_EARTH = 2
BODY_MARS = 3
BODY_JUPITER = 4
BODY_SATURN = 5
BODY_URANUS = 6
BODY_NEPTUNE = 7
BODY_PLUTO = 8
BODY_SUN = 9
BODY_MOON = 10

BodyName = [
    'Mercury',
    'Venus',
    'Earth',
    'Mars',
    'Jupiter',
    'Saturn',
    'Uranus',
    'Neptune',
    'Pluto',
    'Sun',
    'Moon',
]

def BodyCode(name):
    return BodyName.index(name)

def _IsSuperiorPlanet(body):
    return body in [BODY_MARS, BODY_JUPITER, BODY_SATURN, BODY_URANUS, BODY_NEPTUNE, BODY_PLUTO]

_PlanetOrbitalPeriod = [
    87.969,
    224.701,
    _EARTH_ORBITAL_PERIOD,
    686.980,
    4332.589,
    10759.22,
    30685.4,
    60189.0,
    90560.0
]

class Error(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class EarthNotAllowedError(Error):
    def __init__(self):
        Error.__init__(self, 'The Earth is not allowed as the body.')

class InvalidBodyError(Error):
    def __init__(self):
        Error.__init__(self, 'Invalid astronomical body.')

class BadVectorError(Error):
    def __init__(self):
        Error.__init__(self, 'Vector is too small to have a direction.')

class InternalError(Error):
    def __init__(self):
        Error.__init__(self, 'Internal error - please report issue at https://github.com/cosinekitty/astronomy/issues')

class NoConvergeError(Error):
    def __init__(self):
        Error.__init__(self, 'Numeric solver did not converge - please report issue at https://github.com/cosinekitty/astronomy/issues')

def _SynodicPeriod(body):
    if body == BODY_EARTH:
        raise EarthNotAllowedError()
    if body < 0 or body >= len(_PlanetOrbitalPeriod):
        raise InvalidBodyError()
    if body == BODY_MOON:
        return _MEAN_SYNODIC_MONTH
    return abs(_EARTH_ORBITAL_PERIOD / (_EARTH_ORBITAL_PERIOD/_PlanetOrbitalPeriod[body] - 1.0))

def _AngleBetween(a, b):
    r = a.Length() * b.Length()
    if r < 1.0e-8:
        return BadVectorError()
    dot = (a.x*b.x + a.y*b.y + a.z*b.z) / r
    if dot <= -1.0:
        return 180.0
    if dot >= +1.0:
        return 0.0
    return _RAD2DEG * math.acos(dot)

class _delta_t_entry_t:
    def __init__(self, mjd, dt):
        self.mjd = mjd
        self.dt = dt

_DT = [
_delta_t_entry_t(-72638.0, 38),
_delta_t_entry_t(-65333.0, 26),
_delta_t_entry_t(-58028.0, 21),
_delta_t_entry_t(-50724.0, 21.1),
_delta_t_entry_t(-43419.0, 13.5),
_delta_t_entry_t(-39766.0, 13.7),
_delta_t_entry_t(-36114.0, 14.8),
_delta_t_entry_t(-32461.0, 15.7),
_delta_t_entry_t(-28809.0, 15.6),
_delta_t_entry_t(-25156.0, 13.3),
_delta_t_entry_t(-21504.0, 12.6),
_delta_t_entry_t(-17852.0, 11.2),
_delta_t_entry_t(-14200.0, 11.13),
_delta_t_entry_t(-10547.0, 7.95),
_delta_t_entry_t(-6895.0, 6.22),
_delta_t_entry_t(-3242.0, 6.55),
_delta_t_entry_t(-1416.0, 7.26),
_delta_t_entry_t(410.0, 7.35),
_delta_t_entry_t(2237.0, 5.92),
_delta_t_entry_t(4063.0, 1.04),
_delta_t_entry_t(5889.0, -3.19),
_delta_t_entry_t(7715.0, -5.36),
_delta_t_entry_t(9542.0, -5.74),
_delta_t_entry_t(11368.0, -5.86),
_delta_t_entry_t(13194.0, -6.41),
_delta_t_entry_t(15020.0, -2.70),
_delta_t_entry_t(16846.0, 3.92),
_delta_t_entry_t(18672.0, 10.38),
_delta_t_entry_t(20498.0, 17.19),
_delta_t_entry_t(22324.0, 21.41),
_delta_t_entry_t(24151.0, 23.63),
_delta_t_entry_t(25977.0, 24.02),
_delta_t_entry_t(27803.0, 23.91),
_delta_t_entry_t(29629.0, 24.35),
_delta_t_entry_t(31456.0, 26.76),
_delta_t_entry_t(33282.0, 29.15),
_delta_t_entry_t(35108.0, 31.07),
_delta_t_entry_t(36934.0, 33.150),
_delta_t_entry_t(38761.0, 35.738),
_delta_t_entry_t(40587.0, 40.182),
_delta_t_entry_t(42413.0, 45.477),
_delta_t_entry_t(44239.0, 50.540),
_delta_t_entry_t(44605.0, 51.3808),
_delta_t_entry_t(44970.0, 52.1668),
_delta_t_entry_t(45335.0, 52.9565),
_delta_t_entry_t(45700.0, 53.7882),
_delta_t_entry_t(46066.0, 54.3427),
_delta_t_entry_t(46431.0, 54.8712),
_delta_t_entry_t(46796.0, 55.3222),
_delta_t_entry_t(47161.0, 55.8197),
_delta_t_entry_t(47527.0, 56.3000),
_delta_t_entry_t(47892.0, 56.8553),
_delta_t_entry_t(48257.0, 57.5653),
_delta_t_entry_t(48622.0, 58.3092),
_delta_t_entry_t(48988.0, 59.1218),
_delta_t_entry_t(49353.0, 59.9845),
_delta_t_entry_t(49718.0, 60.7853),
_delta_t_entry_t(50083.0, 61.6287),
_delta_t_entry_t(50449.0, 62.2950),
_delta_t_entry_t(50814.0, 62.9659),
_delta_t_entry_t(51179.0, 63.4673),
_delta_t_entry_t(51544.0, 63.8285),
_delta_t_entry_t(51910.0, 64.0908),
_delta_t_entry_t(52275.0, 64.2998),
_delta_t_entry_t(52640.0, 64.4734),
_delta_t_entry_t(53005.0, 64.5736),
_delta_t_entry_t(53371.0, 64.6876),
_delta_t_entry_t(53736.0, 64.8452),
_delta_t_entry_t(54101.0, 65.1464),
_delta_t_entry_t(54466.0, 65.4573),
_delta_t_entry_t(54832.0, 65.7768),
_delta_t_entry_t(55197.0, 66.0699),
_delta_t_entry_t(55562.0, 66.3246),
_delta_t_entry_t(55927.0, 66.6030),
_delta_t_entry_t(56293.0, 66.9069),
_delta_t_entry_t(56658.0, 67.2810),
_delta_t_entry_t(57023.0, 67.6439),
_delta_t_entry_t(57388.0, 68.1024),
_delta_t_entry_t(57754.0, 68.5927),
_delta_t_entry_t(58119.0, 68.9676),
_delta_t_entry_t(58484.0, 69.2201),
_delta_t_entry_t(58849.0, 69.87),
_delta_t_entry_t(59214.0, 70.39),
_delta_t_entry_t(59580.0, 70.91),
_delta_t_entry_t(59945.0, 71.40),
_delta_t_entry_t(60310.0, 71.88),
_delta_t_entry_t(60675.0, 72.36),
_delta_t_entry_t(61041.0, 72.83),
_delta_t_entry_t(61406.0, 73.32),
_delta_t_entry_t(61680.0, 73.66)
]

def _DeltaT(mjd):
    if mjd <= _DT[0].mjd:
        return _DT[0].dt
    if mjd >= _DT[-1].mjd:
        return _DT[-1].dt
    # Do a binary search to find the pair of indexes this mjd lies between.
    lo = 0
    hi = len(_DT) - 2   # Make sure there is always an array element after the one we are looking at.
    while True:
        if lo > hi:
            # This should never happen unless there is a bug in the binary search.
            raise Error('Could not find delta-t value.')
        c = (lo + hi) // 2
        if mjd < _DT[c].mjd:
            hi = c-1
        elif mjd > _DT[c+1].mjd:
            lo = c+1
        else:
            frac = (mjd - _DT[c].mjd) / (_DT[c+1].mjd - _DT[c].mjd)
            return _DT[c].dt + frac*(_DT[c+1].dt - _DT[c].dt)

def _TerrestrialTime(ut):
    return ut + _DeltaT(ut + _Y2000_IN_MJD) / 86400.0

class Time:
    def __init__(self, ut):
        self.ut = ut
        self.tt = _TerrestrialTime(ut)
        self.etilt = None

    @staticmethod
    def Make(year, month, day, hour, minute, second):
        micro = round((second % 1) * 1000000)
        second = math.floor(second - micro/1000000)
        d = datetime.datetime(year, month, day, hour, minute, second, micro)
        ut = (d - _EPOCH).total_seconds() / 86400
        return Time(ut)

    @staticmethod
    def Now():
        ut = (datetime.datetime.utcnow() - _EPOCH).total_seconds() / 86400.0
        return Time(ut)

    def AddDays(self, days):
        return Time(self.ut + days)

    def __str__(self):
        millis = round(self.ut * 86400000.0)
        n = _EPOCH + datetime.timedelta(milliseconds=millis)
        return '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:03d}Z'.format(n.year, n.month, n.day, n.hour, n.minute, n.second, math.floor(n.microsecond / 1000))

    def Utc(self):
        return _EPOCH + datetime.timedelta(days=self.ut)

    def _etilt(self):
        # Calculates precession and nutation of the Earth's axis.
        # The calculations are very expensive, so lazy-evaluate and cache
        # the result inside this Time object.
        if self.etilt is None:
            self.etilt = _e_tilt(self)
        return self.etilt


class Observer:
    def __init__(self, latitude, longitude, height=0):
        self.latitude = latitude
        self.longitude = longitude
        self.height = height

_nals_t = [
    [ 0,    0,    0,    0,    1],
    [ 0,    0,    2,   -2,    2],
    [ 0,    0,    2,    0,    2],
    [ 0,    0,    0,    0,    2],
    [ 0,    1,    0,    0,    0],
    [ 0,    1,    2,   -2,    2],
    [ 1,    0,    0,    0,    0],
    [ 0,    0,    2,    0,    1],
    [ 1,    0,    2,    0,    2],
    [ 0,   -1,    2,   -2,    2],
    [ 0,    0,    2,   -2,    1],
    [-1,    0,    2,    0,    2],
    [-1,    0,    0,    2,    0],
    [ 1,    0,    0,    0,    1],
    [-1,    0,    0,    0,    1],
    [-1,    0,    2,    2,    2],
    [ 1,    0,    2,    0,    1],
    [-2,    0,    2,    0,    1],
    [ 0,    0,    0,    2,    0],
    [ 0,    0,    2,    2,    2],
    [ 0,   -2,    2,   -2,    2],
    [-2,    0,    0,    2,    0],
    [ 2,    0,    2,    0,    2],
    [ 1,    0,    2,   -2,    2],
    [-1,    0,    2,    0,    1],
    [ 2,    0,    0,    0,    0],
    [ 0,    0,    2,    0,    0],
    [ 0,    1,    0,    0,    1],
    [-1,    0,    0,    2,    1],
    [ 0,    2,    2,   -2,    2],
    [ 0,    0,   -2,    2,    0],
    [ 1,    0,    0,   -2,    1],
    [ 0,   -1,    0,    0,    1],
    [-1,    0,    2,    2,    1],
    [ 0,    2,    0,    0,    0],
    [ 1,    0,    2,    2,    2],
    [-2,    0,    2,    0,    0],
    [ 0,    1,    2,    0,    2],
    [ 0,    0,    2,    2,    1],
    [ 0,   -1,    2,    0,    2],
    [ 0,    0,    0,    2,    1],
    [ 1,    0,    2,   -2,    1],
    [ 2,    0,    2,   -2,    2],
    [-2,    0,    0,    2,    1],
    [ 2,    0,    2,    0,    1],
    [ 0,   -1,    2,   -2,    1],
    [ 0,    0,    0,   -2,    1],
    [-1,   -1,    0,    2,    0],
    [ 2,    0,    0,   -2,    1],
    [ 1,    0,    0,    2,    0],
    [ 0,    1,    2,   -2,    1],
    [ 1,   -1,    0,    0,    0],
    [-2,    0,    2,    0,    2],
    [ 3,    0,    2,    0,    2],
    [ 0,   -1,    0,    2,    0],
    [ 1,   -1,    2,    0,    2],
    [ 0,    0,    0,    1,    0],
    [-1,   -1,    2,    2,    2],
    [-1,    0,    2,    0,    0],
    [ 0,   -1,    2,    2,    2],
    [-2,    0,    0,    0,    1],
    [ 1,    1,    2,    0,    2],
    [ 2,    0,    0,    0,    1],
    [-1,    1,    0,    1,    0],
    [ 1,    1,    0,    0,    0],
    [ 1,    0,    2,    0,    0],
    [-1,    0,    2,   -2,    1],
    [ 1,    0,    0,    0,    2],
    [-1,    0,    0,    1,    0],
    [ 0,    0,    2,    1,    2],
    [-1,    0,    2,    4,    2],
    [-1,    1,    0,    1,    1],
    [ 0,   -2,    2,   -2,    1],
    [ 1,    0,    2,    2,    1],
    [-2,    0,    2,    2,    2],
    [-1,    0,    0,    0,    2],
    [ 1,    1,    2,   -2,    2]
]

_cls_t = [
    [-172064161.0, -174666.0,  33386.0, 92052331.0,  9086.0, 15377.0],
    [ -13170906.0,   -1675.0, -13696.0,  5730336.0, -3015.0, -4587.0],
    [  -2276413.0,    -234.0,   2796.0,   978459.0,  -485.0,  1374.0],
    [   2074554.0,     207.0,   -698.0,  -897492.0,   470.0,  -291.0],
    [   1475877.0,   -3633.0,  11817.0,    73871.0,  -184.0, -1924.0],
    [   -516821.0,    1226.0,   -524.0,   224386.0,  -677.0,  -174.0],
    [    711159.0,      73.0,   -872.0,    -6750.0,     0.0,   358.0],
    [   -387298.0,    -367.0,    380.0,   200728.0,    18.0,   318.0],
    [   -301461.0,     -36.0,    816.0,   129025.0,   -63.0,   367.0],
    [    215829.0,    -494.0,    111.0,   -95929.0,   299.0,   132.0],
    [    128227.0,     137.0,    181.0,   -68982.0,    -9.0,    39.0],
    [    123457.0,      11.0,     19.0,   -53311.0,    32.0,    -4.0],
    [    156994.0,      10.0,   -168.0,    -1235.0,     0.0,    82.0],
    [     63110.0,      63.0,     27.0,   -33228.0,     0.0,    -9.0],
    [    -57976.0,     -63.0,   -189.0,    31429.0,     0.0,   -75.0],
    [    -59641.0,     -11.0,    149.0,    25543.0,   -11.0,    66.0],
    [    -51613.0,     -42.0,    129.0,    26366.0,     0.0,    78.0],
    [     45893.0,      50.0,     31.0,   -24236.0,   -10.0,    20.0],
    [     63384.0,      11.0,   -150.0,    -1220.0,     0.0,    29.0],
    [    -38571.0,      -1.0,    158.0,    16452.0,   -11.0,    68.0],
    [     32481.0,       0.0,      0.0,   -13870.0,     0.0,     0.0],
    [    -47722.0,       0.0,    -18.0,      477.0,     0.0,   -25.0],
    [    -31046.0,      -1.0,    131.0,    13238.0,   -11.0,    59.0],
    [     28593.0,       0.0,     -1.0,   -12338.0,    10.0,    -3.0],
    [     20441.0,      21.0,     10.0,   -10758.0,     0.0,    -3.0],
    [     29243.0,       0.0,    -74.0,     -609.0,     0.0,    13.0],
    [     25887.0,       0.0,    -66.0,     -550.0,     0.0,    11.0],
    [    -14053.0,     -25.0,     79.0,     8551.0,    -2.0,   -45.0],
    [     15164.0,      10.0,     11.0,    -8001.0,     0.0,    -1.0],
    [    -15794.0,      72.0,    -16.0,     6850.0,   -42.0,    -5.0],
    [     21783.0,       0.0,     13.0,     -167.0,     0.0,    13.0],
    [    -12873.0,     -10.0,    -37.0,     6953.0,     0.0,   -14.0],
    [    -12654.0,      11.0,     63.0,     6415.0,     0.0,    26.0],
    [    -10204.0,       0.0,     25.0,     5222.0,     0.0,    15.0],
    [     16707.0,     -85.0,    -10.0,      168.0,    -1.0,    10.0],
    [     -7691.0,       0.0,     44.0,     3268.0,     0.0,    19.0],
    [    -11024.0,       0.0,    -14.0,      104.0,     0.0,     2.0],
    [      7566.0,     -21.0,    -11.0,    -3250.0,     0.0,    -5.0],
    [     -6637.0,     -11.0,     25.0,     3353.0,     0.0,    14.0],
    [     -7141.0,      21.0,      8.0,     3070.0,     0.0,     4.0],
    [     -6302.0,     -11.0,      2.0,     3272.0,     0.0,     4.0],
    [      5800.0,      10.0,      2.0,    -3045.0,     0.0,    -1.0],
    [      6443.0,       0.0,     -7.0,    -2768.0,     0.0,    -4.0],
    [     -5774.0,     -11.0,    -15.0,     3041.0,     0.0,    -5.0],
    [     -5350.0,       0.0,     21.0,     2695.0,     0.0,    12.0],
    [     -4752.0,     -11.0,     -3.0,     2719.0,     0.0,    -3.0],
    [     -4940.0,     -11.0,    -21.0,     2720.0,     0.0,    -9.0],
    [      7350.0,       0.0,     -8.0,      -51.0,     0.0,     4.0],
    [      4065.0,       0.0,      6.0,    -2206.0,     0.0,     1.0],
    [      6579.0,       0.0,    -24.0,     -199.0,     0.0,     2.0],
    [      3579.0,       0.0,      5.0,    -1900.0,     0.0,     1.0],
    [      4725.0,       0.0,     -6.0,      -41.0,     0.0,     3.0],
    [     -3075.0,       0.0,     -2.0,     1313.0,     0.0,    -1.0],
    [     -2904.0,       0.0,     15.0,     1233.0,     0.0,     7.0],
    [      4348.0,       0.0,    -10.0,      -81.0,     0.0,     2.0],
    [     -2878.0,       0.0,      8.0,     1232.0,     0.0,     4.0],
    [     -4230.0,       0.0,      5.0,      -20.0,     0.0,    -2.0],
    [     -2819.0,       0.0,      7.0,     1207.0,     0.0,     3.0],
    [     -4056.0,       0.0,      5.0,       40.0,     0.0,    -2.0],
    [     -2647.0,       0.0,     11.0,     1129.0,     0.0,     5.0],
    [     -2294.0,       0.0,    -10.0,     1266.0,     0.0,    -4.0],
    [      2481.0,       0.0,     -7.0,    -1062.0,     0.0,    -3.0],
    [      2179.0,       0.0,     -2.0,    -1129.0,     0.0,    -2.0],
    [      3276.0,       0.0,      1.0,       -9.0,     0.0,     0.0],
    [     -3389.0,       0.0,      5.0,       35.0,     0.0,    -2.0],
    [      3339.0,       0.0,    -13.0,     -107.0,     0.0,     1.0],
    [     -1987.0,       0.0,     -6.0,     1073.0,     0.0,    -2.0],
    [     -1981.0,       0.0,      0.0,      854.0,     0.0,     0.0],
    [      4026.0,       0.0,   -353.0,     -553.0,     0.0,  -139.0],
    [      1660.0,       0.0,     -5.0,     -710.0,     0.0,    -2.0],
    [     -1521.0,       0.0,      9.0,      647.0,     0.0,     4.0],
    [      1314.0,       0.0,      0.0,     -700.0,     0.0,     0.0],
    [     -1283.0,       0.0,      0.0,      672.0,     0.0,     0.0],
    [     -1331.0,       0.0,      8.0,      663.0,     0.0,     4.0],
    [      1383.0,       0.0,     -2.0,     -594.0,     0.0,    -2.0],
    [      1405.0,       0.0,      4.0,     -610.0,     0.0,     2.0],
    [      1290.0,       0.0,      0.0,     -556.0,     0.0,     0.0]
]

class _iau2000b:
    def __init__(self, time):
        t = time.tt / 36525
        el  = ((485868.249036 + t * 1717915923.2178) % _ASEC360) * _ASEC2RAD
        elp = ((1287104.79305 + t * 129596581.0481)  % _ASEC360) * _ASEC2RAD
        f   = ((335779.526232 + t * 1739527262.8478) % _ASEC360) * _ASEC2RAD
        d   = ((1072260.70369 + t * 1602961601.2090) % _ASEC360) * _ASEC2RAD
        om  = ((450160.398036 - t * 6962890.5431)    % _ASEC360) * _ASEC2RAD
        dp = 0
        de = 0
        i = 76
        while i >= 0:
            arg = (_nals_t[i][0]*el + _nals_t[i][1]*elp + _nals_t[i][2]*f + _nals_t[i][3]*d + _nals_t[i][4]*om) % _PI2
            sarg = math.sin(arg)
            carg = math.cos(arg)
            dp += (_cls_t[i][0] + _cls_t[i][1] * t)*sarg + _cls_t[i][2]*carg
            de += (_cls_t[i][3] + _cls_t[i][4] * t)*carg + _cls_t[i][5]*sarg
            i -= 1
        self.dpsi = -0.000135 + (dp * 1.0e-7)
        self.deps = +0.000388 + (de * 1.0e-7)

def _mean_obliq(tt):
    t = tt / 36525
    asec = (
        (((( -  0.0000000434   * t
             -  0.000000576  ) * t
             +  0.00200340   ) * t
             -  0.0001831    ) * t
             - 46.836769     ) * t + 84381.406
    )
    return asec / 3600.0

class _e_tilt:
    def __init__(self, time):
        e = _iau2000b(time)
        self.dpsi = e.dpsi
        self.deps = e.deps
        self.mobl = _mean_obliq(time.tt)
        self.tobl = self.mobl + (e.deps / 3600.0)
        self.tt = time.tt
        self.ee = e.dpsi * math.cos(self.mobl * _DEG2RAD) / 15.0

def _ecl2equ_vec(time, ecl):
    obl = _mean_obliq(time.tt) * _DEG2RAD
    cos_obl = math.cos(obl)
    sin_obl = math.sin(obl)
    return [
        ecl[0],
        ecl[1]*cos_obl - ecl[2]*sin_obl,
        ecl[1]*sin_obl + ecl[2]*cos_obl
    ]

def _precession(tt1, pos1, tt2):
    eps0 = 84381.406
    if tt1 != 0 and tt2 != 0:
        raise Error('One of (tt1, tt2) must be zero.')
    t = (tt2 - tt1) / 36525
    if tt2 == 0:
        t = -t

    psia  = (((((-    0.0000000951  * t
                 +    0.000132851 ) * t
                 -    0.00114045  ) * t
                 -    1.0790069   ) * t
                 + 5038.481507    ) * t)

    omegaa = (((((+   0.0000003337  * t
                 -    0.000000467 ) * t
                 -    0.00772503  ) * t
                 +    0.0512623   ) * t
                 -    0.025754    ) * t + eps0)

    chia  = (((((-    0.0000000560  * t
                 +    0.000170663 ) * t
                 -    0.00121197  ) * t
                 -    2.3814292   ) * t
                 +   10.556403    ) * t)

    eps0 *= _ASEC2RAD
    psia *= _ASEC2RAD
    omegaa *= _ASEC2RAD
    chia *= _ASEC2RAD

    sa = math.sin(eps0)
    ca = math.cos(eps0)
    sb = math.sin(-psia)
    cb = math.cos(-psia)
    sc = math.sin(-omegaa)
    cc = math.cos(-omegaa)
    sd = math.sin(chia)
    cd = math.cos(chia)

    xx =  cd * cb - sb * sd * cc
    yx =  cd * sb * ca + sd * cc * cb * ca - sa * sd * sc
    zx =  cd * sb * sa + sd * cc * cb * sa + ca * sd * sc
    xy = -sd * cb - sb * cd * cc
    yy = -sd * sb * ca + cd * cc * cb * ca - sa * cd * sc
    zy = -sd * sb * sa + cd * cc * cb * sa + ca * cd * sc
    xz =  sb * sc
    yz = -sc * cb * ca - sa * cc
    zz = -sc * cb * sa + cc * ca
    if tt2 == 0.0:
        # Perform rotation from other epoch to J2000.0.
        return [
            xx * pos1[0] + xy * pos1[1] + xz * pos1[2],
            yx * pos1[0] + yy * pos1[1] + yz * pos1[2],
            zx * pos1[0] + zy * pos1[1] + zz * pos1[2]
        ]

    # Perform rotation from J2000.0 to other epoch.
    return [
        xx * pos1[0] + yx * pos1[1] + zx * pos1[2],
        xy * pos1[0] + yy * pos1[1] + zy * pos1[2],
        xz * pos1[0] + yz * pos1[1] + zz * pos1[2]
    ]

class Equatorial:
    def __init__(self, ra, dec, dist):
        self.ra = ra
        self.dec = dec
        self.dist = dist

def _vector2radec(pos):
    xyproj = pos[0]*pos[0] + pos[1]*pos[1]
    dist = math.sqrt(xyproj + pos[2]*pos[2])
    if xyproj == 0.0:
        if pos[2] == 0.0:
            # Indeterminate coordinates: pos vector has zero length.
            raise Error('Cannot convert vector to polar coordinates')
        ra = 0.0
        if pos[2] < 0.0:
            dec = -90.0
        else:
            dec = +90.0
    else:
        ra = math.atan2(pos[1], pos[0]) / (_DEG2RAD * 15)
        if ra < 0:
            ra += 24
        dec = _RAD2DEG * math.atan2(pos[2], math.sqrt(xyproj))
    return Equatorial(ra, dec, dist)


def _nutation(time, direction, inpos):
    tilt = time._etilt()
    oblm = tilt.mobl * _DEG2RAD
    oblt = tilt.tobl * _DEG2RAD
    psi = tilt.dpsi * _ASEC2RAD
    cobm = math.cos(oblm)
    sobm = math.sin(oblm)
    cobt = math.cos(oblt)
    sobt = math.sin(oblt)
    cpsi = math.cos(psi)
    spsi = math.sin(psi)

    xx = cpsi
    yx = -spsi * cobm
    zx = -spsi * sobm
    xy = spsi * cobt
    yy = cpsi * cobm * cobt + sobm * sobt
    zy = cpsi * sobm * cobt - cobm * sobt
    xz = spsi * sobt
    yz = cpsi * cobm * sobt - sobm * cobt
    zz = cpsi * sobm * sobt + cobm * cobt

    if direction == 0:
        # forward rotation
        return [
            xx * inpos[0] + yx * inpos[1] + zx * inpos[2],
            xy * inpos[0] + yy * inpos[1] + zy * inpos[2],
            xz * inpos[0] + yz * inpos[1] + zz * inpos[2]
        ]

    # inverse rotation
    return [
        xx * inpos[0] + xy * inpos[1] + xz * inpos[2],
        yx * inpos[0] + yy * inpos[1] + yz * inpos[2],
        zx * inpos[0] + zy * inpos[1] + zz * inpos[2]
    ]

def _era(time):        # Earth Rotation Angle
    thet1 = 0.7790572732640 + 0.00273781191135448 * time.ut
    thet3 = time.ut % 1.0
    theta = 360.0 * ((thet1 + thet3) % 1.0)
    if theta < 0.0:
        theta += 360.0
    return theta


def _sidereal_time(time):
    t = time.tt / 36525.0
    eqeq = 15.0 * time._etilt().ee    # Replace with eqeq=0 to get GMST instead of GAST (if we ever need it)
    theta = _era(time)
    st = (eqeq + 0.014506 +
        (((( -    0.0000000368   * t
            -    0.000029956  ) * t
            -    0.00000044   ) * t
            +    1.3915817    ) * t
            + 4612.156534     ) * t)
    gst = ((st/3600.0 + theta) % 360.0) / 15.0
    if gst < 0.0:
        gst += 24.0
    return gst


def _terra(observer, st):
    erad_km = _ERAD / 1000.0
    df = 1.0 - 0.003352819697896    # flattening of the Earth
    df2 = df * df
    phi = observer.latitude * _DEG2RAD
    sinphi = math.sin(phi)
    cosphi = math.cos(phi)
    c = 1.0 / math.sqrt(cosphi*cosphi + df2*sinphi*sinphi)
    s = df2 * c
    ht_km = observer.height / 1000.0
    ach = erad_km*c + ht_km
    ash = erad_km*s + ht_km
    stlocl = (15.0*st + observer.longitude) * _DEG2RAD
    sinst = math.sin(stlocl)
    cosst = math.cos(stlocl)
    return [
        ach * cosphi * cosst / _KM_PER_AU,
        ach * cosphi * sinst / _KM_PER_AU,
        ash * sinphi / _KM_PER_AU
    ]

def _geo_pos(time, observer):
    gast = _sidereal_time(time)
    pos1 = _terra(observer, gast)
    pos2 = _nutation(time, -1, pos1)
    outpos = _precession(time.tt, pos2, 0.0)
    return outpos

def _spin(angle, pos1):
    angr = angle * _DEG2RAD
    cosang = math.cos(angr)
    sinang = math.sin(angr)
    return [
        +cosang*pos1[0] + sinang*pos1[1],
        -sinang*pos1[0] + cosang*pos1[1],
        pos1[2]
    ]

#----------------------------------------------------------------------------
# BEGIN CalcMoon

class _Array1:
    def __init__(self, xmin, xmax):
        self.min = xmin
        self.array = [0] * (xmax - xmin + 1)

    def __getitem__(self, key):
        return self.array[key - self.min]

    def __setitem__(self, key, value):
        self.array[key - self.min] = value

class _Array2:
    def __init__(self, xmin, xmax, ymin, ymax):
        self.min = xmin
        self.array = [_Array1(ymin, ymax) for i in range(xmax - xmin + 1)]

    def __getitem__(self, key):
        return self.array[key - self.min]

    def __setitem__(self, key, value):
        self.array[key - self.min] = value

class _moonpos:
    def __init__(self, lon, lat, dist):
        self.geo_eclip_lon = lon
        self.geo_eclip_lat = lat
        self.distance_au = dist

def _CalcMoon(time):
    T = time.tt / 36525
    co = _Array2(-6, 6, 1, 4)
    si = _Array2(-6, 6, 1, 4)

    def AddThe(c1, s1, c2, s2):
        return (c1*c2 - s1*s2, s1*c2 + c1*s2)

    def Sine(phi):
        return math.sin(_PI2 * phi)

    def Frac(x):
        return x - math.floor(x)

    T2 = T*T
    DLAM = 0
    DS = 0
    GAM1C = 0
    SINPI = 3422.7000
    S1 = Sine(0.19833+0.05611*T)
    S2 = Sine(0.27869+0.04508*T)
    S3 = Sine(0.16827-0.36903*T)
    S4 = Sine(0.34734-5.37261*T)
    S5 = Sine(0.10498-5.37899*T)
    S6 = Sine(0.42681-0.41855*T)
    S7 = Sine(0.14943-5.37511*T)
    DL0 = 0.84*S1+0.31*S2+14.27*S3+ 7.26*S4+ 0.28*S5+0.24*S6
    DL  = 2.94*S1+0.31*S2+14.27*S3+ 9.34*S4+ 1.12*S5+0.83*S6
    DLS =-6.40*S1                                   -1.89*S6
    DF  = 0.21*S1+0.31*S2+14.27*S3-88.70*S4-15.30*S5+0.24*S6-1.86*S7
    DD  = DL0-DLS
    DGAM  = ((-3332E-9 * Sine(0.59734-5.37261*T)
               -539E-9 * Sine(0.35498-5.37899*T)
                -64E-9 * Sine(0.39943-5.37511*T)))

    L0 = _PI2*Frac(0.60643382+1336.85522467*T-0.00000313*T2) + DL0/_ARC
    L  = _PI2*Frac(0.37489701+1325.55240982*T+0.00002565*T2) + DL /_ARC
    LS = _PI2*Frac(0.99312619+  99.99735956*T-0.00000044*T2) + DLS/_ARC
    F  = _PI2*Frac(0.25909118+1342.22782980*T-0.00000892*T2) + DF /_ARC
    D  = _PI2*Frac(0.82736186+1236.85308708*T-0.00000397*T2) + DD /_ARC

    I = 1
    while I <= 4:
        if I == 1:
            ARG=L; MAX=4; FAC=1.000002208
        elif I == 2:
            ARG=LS; MAX=3; FAC=0.997504612-0.002495388*T
        elif I == 3:
            ARG=F; MAX=4; FAC=1.000002708+139.978*DGAM
        else:
            ARG=D; MAX=6; FAC=1.0

        co[0][I] = 1
        co[1][I] = math.cos(ARG) * FAC
        si[0][I] = 0
        si[1][I] = math.sin(ARG) * FAC

        J = 2
        while J <= MAX:
            co[J][I], si[J][I] = AddThe(co[J-1][I], si[J-1][I], co[1][I], si[1][I])
            J += 1

        J = 1
        while J <= MAX:
            co[-J][I] = +co[J][I]
            si[-J][I] = -si[J][I]
            J += 1

        I += 1

    def Term(p, q, r, s):
        result = (1, 0)
        I = [None, p, q, r, s]
        k = 1
        while k <= 4:
            if I[k] != 0:
                result = AddThe(result[0], result[1], co[I[k]][k], si[I[k]][k])
            k += 1
        return result

    def AddSol(coeffl, coeffs, coeffg, coeffp, p, q, r, s):
        nonlocal DLAM, DS, GAM1C, SINPI
        result = Term(p, q, r, s)
        DLAM += coeffl * result[1]
        DS += coeffs * result[1]
        GAM1C += coeffg * result[0]
        SINPI += coeffp * result[0]

    AddSol(    13.902,   14.06,-0.001,   0.2607,0, 0, 0, 4)
    AddSol(     0.403,   -4.01,+0.394,   0.0023,0, 0, 0, 3)
    AddSol(  2369.912, 2373.36,+0.601,  28.2333,0, 0, 0, 2)
    AddSol(  -125.154, -112.79,-0.725,  -0.9781,0, 0, 0, 1)
    AddSol(     1.979,    6.98,-0.445,   0.0433,1, 0, 0, 4)
    AddSol(   191.953,  192.72,+0.029,   3.0861,1, 0, 0, 2)
    AddSol(    -8.466,  -13.51,+0.455,  -0.1093,1, 0, 0, 1)
    AddSol( 22639.500,22609.07,+0.079, 186.5398,1, 0, 0, 0)
    AddSol(    18.609,    3.59,-0.094,   0.0118,1, 0, 0,-1)
    AddSol( -4586.465,-4578.13,-0.077,  34.3117,1, 0, 0,-2)
    AddSol(    +3.215,    5.44,+0.192,  -0.0386,1, 0, 0,-3)
    AddSol(   -38.428,  -38.64,+0.001,   0.6008,1, 0, 0,-4)
    AddSol(    -0.393,   -1.43,-0.092,   0.0086,1, 0, 0,-6)
    AddSol(    -0.289,   -1.59,+0.123,  -0.0053,0, 1, 0, 4)
    AddSol(   -24.420,  -25.10,+0.040,  -0.3000,0, 1, 0, 2)
    AddSol(    18.023,   17.93,+0.007,   0.1494,0, 1, 0, 1)
    AddSol(  -668.146, -126.98,-1.302,  -0.3997,0, 1, 0, 0)
    AddSol(     0.560,    0.32,-0.001,  -0.0037,0, 1, 0,-1)
    AddSol(  -165.145, -165.06,+0.054,   1.9178,0, 1, 0,-2)
    AddSol(    -1.877,   -6.46,-0.416,   0.0339,0, 1, 0,-4)
    AddSol(     0.213,    1.02,-0.074,   0.0054,2, 0, 0, 4)
    AddSol(    14.387,   14.78,-0.017,   0.2833,2, 0, 0, 2)
    AddSol(    -0.586,   -1.20,+0.054,  -0.0100,2, 0, 0, 1)
    AddSol(   769.016,  767.96,+0.107,  10.1657,2, 0, 0, 0)
    AddSol(    +1.750,    2.01,-0.018,   0.0155,2, 0, 0,-1)
    AddSol(  -211.656, -152.53,+5.679,  -0.3039,2, 0, 0,-2)
    AddSol(    +1.225,    0.91,-0.030,  -0.0088,2, 0, 0,-3)
    AddSol(   -30.773,  -34.07,-0.308,   0.3722,2, 0, 0,-4)
    AddSol(    -0.570,   -1.40,-0.074,   0.0109,2, 0, 0,-6)
    AddSol(    -2.921,  -11.75,+0.787,  -0.0484,1, 1, 0, 2)
    AddSol(    +1.267,    1.52,-0.022,   0.0164,1, 1, 0, 1)
    AddSol(  -109.673, -115.18,+0.461,  -0.9490,1, 1, 0, 0)
    AddSol(  -205.962, -182.36,+2.056,  +1.4437,1, 1, 0,-2)
    AddSol(     0.233,    0.36, 0.012,  -0.0025,1, 1, 0,-3)
    AddSol(    -4.391,   -9.66,-0.471,   0.0673,1, 1, 0,-4)

    AddSol(     0.283,    1.53,-0.111,  +0.0060,1,-1, 0,+4)
    AddSol(    14.577,   31.70,-1.540,  +0.2302,1,-1, 0, 2)
    AddSol(   147.687,  138.76,+0.679,  +1.1528,1,-1, 0, 0)
    AddSol(    -1.089,    0.55,+0.021,   0.0   ,1,-1, 0,-1)
    AddSol(    28.475,   23.59,-0.443,  -0.2257,1,-1, 0,-2)
    AddSol(    -0.276,   -0.38,-0.006,  -0.0036,1,-1, 0,-3)
    AddSol(     0.636,    2.27,+0.146,  -0.0102,1,-1, 0,-4)
    AddSol(    -0.189,   -1.68,+0.131,  -0.0028,0, 2, 0, 2)
    AddSol(    -7.486,   -0.66,-0.037,  -0.0086,0, 2, 0, 0)
    AddSol(    -8.096,  -16.35,-0.740,   0.0918,0, 2, 0,-2)
    AddSol(    -5.741,   -0.04, 0.0  ,  -0.0009,0, 0, 2, 2)
    AddSol(     0.255,    0.0 , 0.0  ,   0.0   ,0, 0, 2, 1)
    AddSol(  -411.608,   -0.20, 0.0  ,  -0.0124,0, 0, 2, 0)
    AddSol(     0.584,    0.84, 0.0  ,  +0.0071,0, 0, 2,-1)
    AddSol(   -55.173,  -52.14, 0.0  ,  -0.1052,0, 0, 2,-2)
    AddSol(     0.254,    0.25, 0.0  ,  -0.0017,0, 0, 2,-3)
    AddSol(    +0.025,   -1.67, 0.0  ,  +0.0031,0, 0, 2,-4)
    AddSol(     1.060,    2.96,-0.166,   0.0243,3, 0, 0,+2)
    AddSol(    36.124,   50.64,-1.300,   0.6215,3, 0, 0, 0)
    AddSol(   -13.193,  -16.40,+0.258,  -0.1187,3, 0, 0,-2)
    AddSol(    -1.187,   -0.74,+0.042,   0.0074,3, 0, 0,-4)
    AddSol(    -0.293,   -0.31,-0.002,   0.0046,3, 0, 0,-6)
    AddSol(    -0.290,   -1.45,+0.116,  -0.0051,2, 1, 0, 2)
    AddSol(    -7.649,  -10.56,+0.259,  -0.1038,2, 1, 0, 0)
    AddSol(    -8.627,   -7.59,+0.078,  -0.0192,2, 1, 0,-2)
    AddSol(    -2.740,   -2.54,+0.022,   0.0324,2, 1, 0,-4)
    AddSol(     1.181,    3.32,-0.212,   0.0213,2,-1, 0,+2)
    AddSol(     9.703,   11.67,-0.151,   0.1268,2,-1, 0, 0)
    AddSol(    -0.352,   -0.37,+0.001,  -0.0028,2,-1, 0,-1)
    AddSol(    -2.494,   -1.17,-0.003,  -0.0017,2,-1, 0,-2)
    AddSol(     0.360,    0.20,-0.012,  -0.0043,2,-1, 0,-4)
    AddSol(    -1.167,   -1.25,+0.008,  -0.0106,1, 2, 0, 0)
    AddSol(    -7.412,   -6.12,+0.117,   0.0484,1, 2, 0,-2)
    AddSol(    -0.311,   -0.65,-0.032,   0.0044,1, 2, 0,-4)
    AddSol(    +0.757,    1.82,-0.105,   0.0112,1,-2, 0, 2)
    AddSol(    +2.580,    2.32,+0.027,   0.0196,1,-2, 0, 0)
    AddSol(    +2.533,    2.40,-0.014,  -0.0212,1,-2, 0,-2)
    AddSol(    -0.344,   -0.57,-0.025,  +0.0036,0, 3, 0,-2)
    AddSol(    -0.992,   -0.02, 0.0  ,   0.0   ,1, 0, 2, 2)
    AddSol(   -45.099,   -0.02, 0.0  ,  -0.0010,1, 0, 2, 0)
    AddSol(    -0.179,   -9.52, 0.0  ,  -0.0833,1, 0, 2,-2)
    AddSol(    -0.301,   -0.33, 0.0  ,   0.0014,1, 0, 2,-4)
    AddSol(    -6.382,   -3.37, 0.0  ,  -0.0481,1, 0,-2, 2)
    AddSol(    39.528,   85.13, 0.0  ,  -0.7136,1, 0,-2, 0)
    AddSol(     9.366,    0.71, 0.0  ,  -0.0112,1, 0,-2,-2)
    AddSol(     0.202,    0.02, 0.0  ,   0.0   ,1, 0,-2,-4)

    AddSol(     0.415,    0.10, 0.0  ,  0.0013,0, 1, 2, 0)
    AddSol(    -2.152,   -2.26, 0.0  , -0.0066,0, 1, 2,-2)
    AddSol(    -1.440,   -1.30, 0.0  , +0.0014,0, 1,-2, 2)
    AddSol(     0.384,   -0.04, 0.0  ,  0.0   ,0, 1,-2,-2)
    AddSol(    +1.938,   +3.60,-0.145, +0.0401,4, 0, 0, 0)
    AddSol(    -0.952,   -1.58,+0.052, -0.0130,4, 0, 0,-2)
    AddSol(    -0.551,   -0.94,+0.032, -0.0097,3, 1, 0, 0)
    AddSol(    -0.482,   -0.57,+0.005, -0.0045,3, 1, 0,-2)
    AddSol(     0.681,    0.96,-0.026,  0.0115,3,-1, 0, 0)
    AddSol(    -0.297,   -0.27, 0.002, -0.0009,2, 2, 0,-2)
    AddSol(     0.254,   +0.21,-0.003,  0.0   ,2,-2, 0,-2)
    AddSol(    -0.250,   -0.22, 0.004,  0.0014,1, 3, 0,-2)
    AddSol(    -3.996,    0.0 , 0.0  , +0.0004,2, 0, 2, 0)
    AddSol(     0.557,   -0.75, 0.0  , -0.0090,2, 0, 2,-2)
    AddSol(    -0.459,   -0.38, 0.0  , -0.0053,2, 0,-2, 2)
    AddSol(    -1.298,    0.74, 0.0  , +0.0004,2, 0,-2, 0)
    AddSol(     0.538,    1.14, 0.0  , -0.0141,2, 0,-2,-2)
    AddSol(     0.263,    0.02, 0.0  ,  0.0   ,1, 1, 2, 0)
    AddSol(     0.426,   +0.07, 0.0  , -0.0006,1, 1,-2,-2)
    AddSol(    -0.304,   +0.03, 0.0  , +0.0003,1,-1, 2, 0)
    AddSol(    -0.372,   -0.19, 0.0  , -0.0027,1,-1,-2, 2)
    AddSol(    +0.418,    0.0 , 0.0  ,  0.0   ,0, 0, 4, 0)
    AddSol(    -0.330,   -0.04, 0.0  ,  0.0   ,3, 0, 2, 0)

    def ADDN(coeffn, p, q, r, s):
        return coeffn * Term(p, q, r, s)[1]

    N = 0
    N += ADDN(-526.069, 0, 0,1,-2)
    N += ADDN(  -3.352, 0, 0,1,-4)
    N += ADDN( +44.297,+1, 0,1,-2)
    N += ADDN(  -6.000,+1, 0,1,-4)
    N += ADDN( +20.599,-1, 0,1, 0)
    N += ADDN( -30.598,-1, 0,1,-2)
    N += ADDN( -24.649,-2, 0,1, 0)
    N += ADDN(  -2.000,-2, 0,1,-2)
    N += ADDN( -22.571, 0,+1,1,-2)
    N += ADDN( +10.985, 0,-1,1,-2)

    DLAM += (
        +0.82*Sine(0.7736  -62.5512*T)+0.31*Sine(0.0466 -125.1025*T)
        +0.35*Sine(0.5785  -25.1042*T)+0.66*Sine(0.4591+1335.8075*T)
        +0.64*Sine(0.3130  -91.5680*T)+1.14*Sine(0.1480+1331.2898*T)
        +0.21*Sine(0.5918+1056.5859*T)+0.44*Sine(0.5784+1322.8595*T)
        +0.24*Sine(0.2275   -5.7374*T)+0.28*Sine(0.2965   +2.6929*T)
        +0.33*Sine(0.3132   +6.3368*T)
    )
    S = F + DS/_ARC
    lat_seconds = (1.000002708 + 139.978*DGAM)*(18518.511+1.189+GAM1C)*math.sin(S) - 6.24*math.sin(3*S) + N
    return _moonpos(
        _PI2 * Frac((L0+DLAM/_ARC) / _PI2),
        (math.pi / (180 * 3600)) * lat_seconds,
        (_ARC * (_ERAD / _AU)) / (0.999953253 * SINPI)
    )

def GeoMoon(time):
    m = _CalcMoon(time)

    # Convert geocentric ecliptic spherical coordinates to Cartesian coordinates.
    dist_cos_lat = m.distance_au * math.cos(m.geo_eclip_lat)
    gepos = [
        dist_cos_lat * math.cos(m.geo_eclip_lon),
        dist_cos_lat * math.sin(m.geo_eclip_lon),
        m.distance_au * math.sin(m.geo_eclip_lat)
    ]

    # Convert ecliptic coordinates to equatorial coordinates, both in mean equinox of date.
    mpos1 = _ecl2equ_vec(time, gepos)

    # Convert from mean equinox of date to J2000.
    mpos2 = _precession(time.tt, mpos1, 0)
    return Vector(mpos2[0], mpos2[1], mpos2[2], time)

# END CalcMoon
#----------------------------------------------------------------------------
# BEGIN VSOP

_vsop = [
    # Mercury
    [
  [
    [
      [4.40250710144, 0.00000000000, 0.00000000000],
      [0.40989414977, 1.48302034195, 26087.90314157420],
      [0.05046294200, 4.47785489551, 52175.80628314840],
      [0.00855346844, 1.16520322459, 78263.70942472259],
      [0.00165590362, 4.11969163423, 104351.61256629678],
      [0.00034561897, 0.77930768443, 130439.51570787099],
      [0.00007583476, 3.71348404924, 156527.41884944518]
    ],
    [
      [26087.90313685529, 0.00000000000, 0.00000000000],
      [0.01131199811, 6.21874197797, 26087.90314157420],
      [0.00292242298, 3.04449355541, 52175.80628314840],
      [0.00075775081, 6.08568821653, 78263.70942472259],
      [0.00019676525, 2.80965111777, 104351.61256629678]
    ]
  ],
  [
    [
      [0.11737528961, 1.98357498767, 26087.90314157420],
      [0.02388076996, 5.03738959686, 52175.80628314840],
      [0.01222839532, 3.14159265359, 0.00000000000],
      [0.00543251810, 1.79644363964, 78263.70942472259],
      [0.00129778770, 4.83232503958, 104351.61256629678],
      [0.00031866927, 1.58088495658, 130439.51570787099],
      [0.00007963301, 4.60972126127, 156527.41884944518]
    ],
    [
      [0.00274646065, 3.95008450011, 26087.90314157420],
      [0.00099737713, 3.14159265359, 0.00000000000]
    ]
  ],
  [
    [
      [0.39528271651, 0.00000000000, 0.00000000000],
      [0.07834131818, 6.19233722598, 26087.90314157420],
      [0.00795525558, 2.95989690104, 52175.80628314840],
      [0.00121281764, 6.01064153797, 78263.70942472259],
      [0.00021921969, 2.77820093972, 104351.61256629678],
      [0.00004354065, 5.82894543774, 130439.51570787099]
    ],
    [
      [0.00217347740, 4.65617158665, 26087.90314157420],
      [0.00044141826, 1.42385544001, 52175.80628314840]
    ]
  ]
],

    # Venus
    [
  [
    [
      [3.17614666774, 0.00000000000, 0.00000000000],
      [0.01353968419, 5.59313319619, 10213.28554621100],
      [0.00089891645, 5.30650047764, 20426.57109242200],
      [0.00005477194, 4.41630661466, 7860.41939243920],
      [0.00003455741, 2.69964447820, 11790.62908865880],
      [0.00002372061, 2.99377542079, 3930.20969621960],
      [0.00001317168, 5.18668228402, 26.29831979980],
      [0.00001664146, 4.25018630147, 1577.34354244780],
      [0.00001438387, 4.15745084182, 9683.59458111640],
      [0.00001200521, 6.15357116043, 30639.85663863300]
    ],
    [
      [10213.28554621638, 0.00000000000, 0.00000000000],
      [0.00095617813, 2.46406511110, 10213.28554621100],
      [0.00007787201, 0.62478482220, 20426.57109242200]
    ]
  ],
  [
    [
      [0.05923638472, 0.26702775812, 10213.28554621100],
      [0.00040107978, 1.14737178112, 20426.57109242200],
      [0.00032814918, 3.14159265359, 0.00000000000]
    ],
    [
      [0.00287821243, 1.88964962838, 10213.28554621100]
    ]
  ],
  [
    [
      [0.72334820891, 0.00000000000, 0.00000000000],
      [0.00489824182, 4.02151831717, 10213.28554621100],
      [0.00001658058, 4.90206728031, 20426.57109242200]
    ],
    [
      [0.00034551041, 0.89198706276, 10213.28554621100]
    ]
  ]
],

    # Earth
    [
  [
    [
      [1.75347045673, 0.00000000000, 0.00000000000],
      [0.03341656453, 4.66925680415, 6283.07584999140],
      [0.00034894275, 4.62610242189, 12566.15169998280],
      [0.00003417572, 2.82886579754, 3.52311834900],
      [0.00003497056, 2.74411783405, 5753.38488489680],
      [0.00003135899, 3.62767041756, 77713.77146812050],
      [0.00002676218, 4.41808345438, 7860.41939243920],
      [0.00002342691, 6.13516214446, 3930.20969621960],
      [0.00001273165, 2.03709657878, 529.69096509460],
      [0.00001324294, 0.74246341673, 11506.76976979360],
      [0.00000901854, 2.04505446477, 26.29831979980],
      [0.00001199167, 1.10962946234, 1577.34354244780],
      [0.00000857223, 3.50849152283, 398.14900340820],
      [0.00000779786, 1.17882681962, 5223.69391980220],
      [0.00000990250, 5.23268072088, 5884.92684658320],
      [0.00000753141, 2.53339052847, 5507.55323866740],
      [0.00000505267, 4.58292599973, 18849.22754997420],
      [0.00000492392, 4.20505711826, 775.52261132400],
      [0.00000356672, 2.91954114478, 0.06731030280],
      [0.00000284125, 1.89869240932, 796.29800681640],
      [0.00000242879, 0.34481445893, 5486.77784317500],
      [0.00000317087, 5.84901948512, 11790.62908865880],
      [0.00000271112, 0.31486255375, 10977.07880469900],
      [0.00000206217, 4.80646631478, 2544.31441988340],
      [0.00000205478, 1.86953770281, 5573.14280143310],
      [0.00000202318, 2.45767790232, 6069.77675455340],
      [0.00000126225, 1.08295459501, 20.77539549240],
      [0.00000155516, 0.83306084617, 213.29909543800]
    ],
    [
      [6283.07584999140, 0.00000000000, 0.00000000000],
      [0.00206058863, 2.67823455808, 6283.07584999140],
      [0.00004303419, 2.63512233481, 12566.15169998280]
    ],
    [
      [0.00008721859, 1.07253635559, 6283.07584999140]
    ]
  ],
  [
    [
    ],
    [
      [0.00227777722, 3.41376620530, 6283.07584999140],
      [0.00003805678, 3.37063423795, 12566.15169998280]
    ]
  ],
  [
    [
      [1.00013988784, 0.00000000000, 0.00000000000],
      [0.01670699632, 3.09846350258, 6283.07584999140],
      [0.00013956024, 3.05524609456, 12566.15169998280],
      [0.00003083720, 5.19846674381, 77713.77146812050],
      [0.00001628463, 1.17387558054, 5753.38488489680],
      [0.00001575572, 2.84685214877, 7860.41939243920],
      [0.00000924799, 5.45292236722, 11506.76976979360],
      [0.00000542439, 4.56409151453, 3930.20969621960],
      [0.00000472110, 3.66100022149, 5884.92684658320]
    ],
    [
      [0.00103018607, 1.10748968172, 6283.07584999140],
      [0.00001721238, 1.06442300386, 12566.15169998280]
    ],
    [
      [0.00004359385, 5.78455133808, 6283.07584999140]
    ]
  ]
],

    # Mars
    [
  [
    [
      [6.20347711581, 0.00000000000, 0.00000000000],
      [0.18656368093, 5.05037100270, 3340.61242669980],
      [0.01108216816, 5.40099836344, 6681.22485339960],
      [0.00091798406, 5.75478744667, 10021.83728009940],
      [0.00027744987, 5.97049513147, 3.52311834900],
      [0.00010610235, 2.93958560338, 2281.23049651060],
      [0.00012315897, 0.84956094002, 2810.92146160520],
      [0.00008926784, 4.15697846427, 0.01725365220],
      [0.00008715691, 6.11005153139, 13362.44970679920],
      [0.00006797556, 0.36462229657, 398.14900340820],
      [0.00007774872, 3.33968761376, 5621.84292321040],
      [0.00003575078, 1.66186505710, 2544.31441988340],
      [0.00004161108, 0.22814971327, 2942.46342329160],
      [0.00003075252, 0.85696614132, 191.44826611160],
      [0.00002628117, 0.64806124465, 3337.08930835080],
      [0.00002937546, 6.07893711402, 0.06731030280],
      [0.00002389414, 5.03896442664, 796.29800681640],
      [0.00002579844, 0.02996736156, 3344.13554504880],
      [0.00001528141, 1.14979301996, 6151.53388830500],
      [0.00001798806, 0.65634057445, 529.69096509460],
      [0.00001264357, 3.62275122593, 5092.15195811580],
      [0.00001286228, 3.06796065034, 2146.16541647520],
      [0.00001546404, 2.91579701718, 1751.53953141600],
      [0.00001024902, 3.69334099279, 8962.45534991020],
      [0.00000891566, 0.18293837498, 16703.06213349900],
      [0.00000858759, 2.40093811940, 2914.01423582380],
      [0.00000832715, 2.46418619474, 3340.59517304760],
      [0.00000832720, 4.49495782139, 3340.62968035200],
      [0.00000712902, 3.66335473479, 1059.38193018920],
      [0.00000748723, 3.82248614017, 155.42039943420],
      [0.00000723861, 0.67497311481, 3738.76143010800],
      [0.00000635548, 2.92182225127, 8432.76438481560],
      [0.00000655162, 0.48864064125, 3127.31333126180],
      [0.00000550474, 3.81001042328, 0.98032106820],
      [0.00000552750, 4.47479317037, 1748.01641306700],
      [0.00000425966, 0.55364317304, 6283.07584999140],
      [0.00000415131, 0.49662285038, 213.29909543800],
      [0.00000472167, 3.62547124025, 1194.44701022460],
      [0.00000306551, 0.38052848348, 6684.74797174860],
      [0.00000312141, 0.99853944405, 6677.70173505060],
      [0.00000293198, 4.22131299634, 20.77539549240],
      [0.00000302375, 4.48618007156, 3532.06069281140],
      [0.00000274027, 0.54222167059, 3340.54511639700],
      [0.00000281079, 5.88163521788, 1349.86740965880],
      [0.00000231183, 1.28242156993, 3870.30339179440],
      [0.00000283602, 5.76885434940, 3149.16416058820],
      [0.00000236117, 5.75503217933, 3333.49887969900],
      [0.00000274033, 0.13372524985, 3340.67973700260],
      [0.00000299395, 2.78323740866, 6254.62666252360]
    ],
    [
      [3340.61242700512, 0.00000000000, 0.00000000000],
      [0.01457554523, 3.60433733236, 3340.61242669980],
      [0.00168414711, 3.92318567804, 6681.22485339960],
      [0.00020622975, 4.26108844583, 10021.83728009940],
      [0.00003452392, 4.73210393190, 3.52311834900],
      [0.00002586332, 4.60670058555, 13362.44970679920],
      [0.00000841535, 4.45864030426, 2281.23049651060]
    ],
    [
      [0.00058152577, 2.04961712429, 3340.61242669980],
      [0.00013459579, 2.45738706163, 6681.22485339960]
    ]
  ],
  [
    [
      [0.03197134986, 3.76832042431, 3340.61242669980],
      [0.00298033234, 4.10616996305, 6681.22485339960],
      [0.00289104742, 0.00000000000, 0.00000000000],
      [0.00031365539, 4.44651053090, 10021.83728009940],
      [0.00003484100, 4.78812549260, 13362.44970679920]
    ],
    [
      [0.00217310991, 6.04472194776, 3340.61242669980],
      [0.00020976948, 3.14159265359, 0.00000000000],
      [0.00012834709, 1.60810667915, 6681.22485339960]
    ]
  ],
  [
    [
      [1.53033488271, 0.00000000000, 0.00000000000],
      [0.14184953160, 3.47971283528, 3340.61242669980],
      [0.00660776362, 3.81783443019, 6681.22485339960],
      [0.00046179117, 4.15595316782, 10021.83728009940],
      [0.00008109733, 5.55958416318, 2810.92146160520],
      [0.00007485318, 1.77239078402, 5621.84292321040],
      [0.00005523191, 1.36436303770, 2281.23049651060],
      [0.00003825160, 4.49407183687, 13362.44970679920],
      [0.00002306537, 0.09081579001, 2544.31441988340],
      [0.00001999396, 5.36059617709, 3337.08930835080],
      [0.00002484394, 4.92545639920, 2942.46342329160],
      [0.00001960195, 4.74249437639, 3344.13554504880],
      [0.00001167119, 2.11260868341, 5092.15195811580],
      [0.00001102816, 5.00908403998, 398.14900340820],
      [0.00000899066, 4.40791133207, 529.69096509460],
      [0.00000992252, 5.83861961952, 6151.53388830500],
      [0.00000807354, 2.10217065501, 1059.38193018920],
      [0.00000797915, 3.44839203899, 796.29800681640],
      [0.00000740975, 1.49906336885, 2146.16541647520]
    ],
    [
      [0.01107433345, 2.03250524857, 3340.61242669980],
      [0.00103175887, 2.37071847807, 6681.22485339960],
      [0.00012877200, 0.00000000000, 0.00000000000],
      [0.00010815880, 2.70888095665, 10021.83728009940]
    ],
    [
      [0.00044242249, 0.47930604954, 3340.61242669980],
      [0.00008138042, 0.86998389204, 6681.22485339960]
    ]
  ]
],

    # Jupiter
    [
  [
    [
      [0.59954691494, 0.00000000000, 0.00000000000],
      [0.09695898719, 5.06191793158, 529.69096509460],
      [0.00573610142, 1.44406205629, 7.11354700080],
      [0.00306389205, 5.41734730184, 1059.38193018920],
      [0.00097178296, 4.14264726552, 632.78373931320],
      [0.00072903078, 3.64042916389, 522.57741809380],
      [0.00064263975, 3.41145165351, 103.09277421860],
      [0.00039806064, 2.29376740788, 419.48464387520],
      [0.00038857767, 1.27231755835, 316.39186965660],
      [0.00027964629, 1.78454591820, 536.80451209540],
      [0.00013589730, 5.77481040790, 1589.07289528380],
      [0.00008246349, 3.58227925840, 206.18554843720],
      [0.00008768704, 3.63000308199, 949.17560896980],
      [0.00007368042, 5.08101194270, 735.87651353180],
      [0.00006263150, 0.02497628807, 213.29909543800],
      [0.00006114062, 4.51319998626, 1162.47470440780],
      [0.00004905396, 1.32084470588, 110.20632121940],
      [0.00005305285, 1.30671216791, 14.22709400160],
      [0.00005305441, 4.18625634012, 1052.26838318840],
      [0.00004647248, 4.69958103684, 3.93215326310],
      [0.00003045023, 4.31676431084, 426.59819087600],
      [0.00002609999, 1.56667394063, 846.08283475120],
      [0.00002028191, 1.06376530715, 3.18139373770],
      [0.00001764763, 2.14148655117, 1066.49547719000],
      [0.00001722972, 3.88036268267, 1265.56747862640],
      [0.00001920945, 0.97168196472, 639.89728631400],
      [0.00001633223, 3.58201833555, 515.46387109300],
      [0.00001431999, 4.29685556046, 625.67019231240],
      [0.00000973272, 4.09764549134, 95.97922721780]
    ],
    [
      [529.69096508814, 0.00000000000, 0.00000000000],
      [0.00489503243, 4.22082939470, 529.69096509460],
      [0.00228917222, 6.02646855621, 7.11354700080],
      [0.00030099479, 4.54540782858, 1059.38193018920],
      [0.00020720920, 5.45943156902, 522.57741809380],
      [0.00012103653, 0.16994816098, 536.80451209540],
      [0.00006067987, 4.42422292017, 103.09277421860],
      [0.00005433968, 3.98480737746, 419.48464387520],
      [0.00004237744, 5.89008707199, 14.22709400160]
    ],
    [
      [0.00047233601, 4.32148536482, 7.11354700080],
      [0.00030649436, 2.92977788700, 529.69096509460],
      [0.00014837605, 3.14159265359, 0.00000000000]
    ]
  ],
  [
    [
      [0.02268615702, 3.55852606721, 529.69096509460],
      [0.00109971634, 3.90809347197, 1059.38193018920],
      [0.00110090358, 0.00000000000, 0.00000000000],
      [0.00008101428, 3.60509572885, 522.57741809380],
      [0.00006043996, 4.25883108339, 1589.07289528380],
      [0.00006437782, 0.30627119215, 536.80451209540]
    ],
    [
      [0.00078203446, 1.52377859742, 529.69096509460]
    ]
  ],
  [
    [
      [5.20887429326, 0.00000000000, 0.00000000000],
      [0.25209327119, 3.49108639871, 529.69096509460],
      [0.00610599976, 3.84115365948, 1059.38193018920],
      [0.00282029458, 2.57419881293, 632.78373931320],
      [0.00187647346, 2.07590383214, 522.57741809380],
      [0.00086792905, 0.71001145545, 419.48464387520],
      [0.00072062974, 0.21465724607, 536.80451209540],
      [0.00065517248, 5.97995884790, 316.39186965660],
      [0.00029134542, 1.67759379655, 103.09277421860],
      [0.00030135335, 2.16132003734, 949.17560896980],
      [0.00023453271, 3.54023522184, 735.87651353180],
      [0.00022283743, 4.19362594399, 1589.07289528380],
      [0.00023947298, 0.27458037480, 7.11354700080],
      [0.00013032614, 2.96042965363, 1162.47470440780],
      [0.00009703360, 1.90669633585, 206.18554843720],
      [0.00012749023, 2.71550286592, 1052.26838318840]
    ],
    [
      [0.01271801520, 2.64937512894, 529.69096509460],
      [0.00061661816, 3.00076460387, 1059.38193018920],
      [0.00053443713, 3.89717383175, 522.57741809380],
      [0.00031185171, 4.88276958012, 536.80451209540],
      [0.00041390269, 0.00000000000, 0.00000000000]
    ]
  ]
],

    # Saturn
    [
  [
    [
      [0.87401354025, 0.00000000000, 0.00000000000],
      [0.11107659762, 3.96205090159, 213.29909543800],
      [0.01414150957, 4.58581516874, 7.11354700080],
      [0.00398379389, 0.52112032699, 206.18554843720],
      [0.00350769243, 3.30329907896, 426.59819087600],
      [0.00206816305, 0.24658372002, 103.09277421860],
      [0.00079271300, 3.84007056878, 220.41264243880],
      [0.00023990355, 4.66976924553, 110.20632121940],
      [0.00016573588, 0.43719228296, 419.48464387520],
      [0.00014906995, 5.76903183869, 316.39186965660],
      [0.00015820290, 0.93809155235, 632.78373931320],
      [0.00014609559, 1.56518472000, 3.93215326310],
      [0.00013160301, 4.44891291899, 14.22709400160],
      [0.00015053543, 2.71669915667, 639.89728631400],
      [0.00013005299, 5.98119023644, 11.04570026390],
      [0.00010725067, 3.12939523827, 202.25339517410],
      [0.00005863206, 0.23656938524, 529.69096509460],
      [0.00005227757, 4.20783365759, 3.18139373770],
      [0.00006126317, 1.76328667907, 277.03499374140],
      [0.00005019687, 3.17787728405, 433.71173787680],
      [0.00004592550, 0.61977744975, 199.07200143640],
      [0.00004005867, 2.24479718502, 63.73589830340],
      [0.00002953796, 0.98280366998, 95.97922721780],
      [0.00003873670, 3.22283226966, 138.51749687070],
      [0.00002461186, 2.03163875071, 735.87651353180],
      [0.00003269484, 0.77492638211, 949.17560896980],
      [0.00001758145, 3.26580109940, 522.57741809380],
      [0.00001640172, 5.50504453050, 846.08283475120],
      [0.00001391327, 4.02333150505, 323.50541665740],
      [0.00001580648, 4.37265307169, 309.27832265580],
      [0.00001123498, 2.83726798446, 415.55249061210],
      [0.00001017275, 3.71700135395, 227.52618943960],
      [0.00000848642, 3.19150170830, 209.36694217490]
    ],
    [
      [213.29909521690, 0.00000000000, 0.00000000000],
      [0.01297370862, 1.82834923978, 213.29909543800],
      [0.00564345393, 2.88499717272, 7.11354700080],
      [0.00093734369, 1.06311793502, 426.59819087600],
      [0.00107674962, 2.27769131009, 206.18554843720],
      [0.00040244455, 2.04108104671, 220.41264243880],
      [0.00019941774, 1.27954390470, 103.09277421860],
      [0.00010511678, 2.74880342130, 14.22709400160],
      [0.00006416106, 0.38238295041, 639.89728631400],
      [0.00004848994, 2.43037610229, 419.48464387520],
      [0.00004056892, 2.92133209468, 110.20632121940],
      [0.00003768635, 3.64965330780, 3.93215326310]
    ],
    [
      [0.00116441330, 1.17988132879, 7.11354700080],
      [0.00091841837, 0.07325195840, 213.29909543800],
      [0.00036661728, 0.00000000000, 0.00000000000],
      [0.00015274496, 4.06493179167, 206.18554843720]
    ]
  ],
  [
    [
      [0.04330678039, 3.60284428399, 213.29909543800],
      [0.00240348302, 2.85238489373, 426.59819087600],
      [0.00084745939, 0.00000000000, 0.00000000000],
      [0.00030863357, 3.48441504555, 220.41264243880],
      [0.00034116062, 0.57297307557, 206.18554843720],
      [0.00014734070, 2.11846596715, 639.89728631400],
      [0.00009916667, 5.79003188904, 419.48464387520],
      [0.00006993564, 4.73604689720, 7.11354700080],
      [0.00004807588, 5.43305312061, 316.39186965660]
    ],
    [
      [0.00198927992, 4.93901017903, 213.29909543800],
      [0.00036947916, 3.14159265359, 0.00000000000],
      [0.00017966989, 0.51979431110, 426.59819087600]
    ]
  ],
  [
    [
      [9.55758135486, 0.00000000000, 0.00000000000],
      [0.52921382865, 2.39226219573, 213.29909543800],
      [0.01873679867, 5.23549604660, 206.18554843720],
      [0.01464663929, 1.64763042902, 426.59819087600],
      [0.00821891141, 5.93520042303, 316.39186965660],
      [0.00547506923, 5.01532618980, 103.09277421860],
      [0.00371684650, 2.27114821115, 220.41264243880],
      [0.00361778765, 3.13904301847, 7.11354700080],
      [0.00140617506, 5.70406606781, 632.78373931320],
      [0.00108974848, 3.29313390175, 110.20632121940],
      [0.00069006962, 5.94099540992, 419.48464387520],
      [0.00061053367, 0.94037691801, 639.89728631400],
      [0.00048913294, 1.55733638681, 202.25339517410],
      [0.00034143772, 0.19519102597, 277.03499374140],
      [0.00032401773, 5.47084567016, 949.17560896980],
      [0.00020936596, 0.46349251129, 735.87651353180]
    ],
    [
      [0.06182981340, 0.25843511480, 213.29909543800],
      [0.00506577242, 0.71114625261, 206.18554843720],
      [0.00341394029, 5.79635741658, 426.59819087600],
      [0.00188491195, 0.47215589652, 220.41264243880],
      [0.00186261486, 3.14159265359, 0.00000000000],
      [0.00143891146, 1.40744822888, 7.11354700080]
    ],
    [
      [0.00436902572, 4.78671677509, 213.29909543800]
    ]
  ]
],

    # Uranus
    [
  [
    [
      [5.48129294297, 0.00000000000, 0.00000000000],
      [0.09260408234, 0.89106421507, 74.78159856730],
      [0.01504247898, 3.62719260920, 1.48447270830],
      [0.00365981674, 1.89962179044, 73.29712585900],
      [0.00272328168, 3.35823706307, 149.56319713460],
      [0.00070328461, 5.39254450063, 63.73589830340],
      [0.00068892678, 6.09292483287, 76.26607127560],
      [0.00061998615, 2.26952066061, 2.96894541660],
      [0.00061950719, 2.85098872691, 11.04570026390],
      [0.00026468770, 3.14152083966, 71.81265315070],
      [0.00025710476, 6.11379840493, 454.90936652730],
      [0.00021078850, 4.36059339067, 148.07872442630],
      [0.00017818647, 1.74436930289, 36.64856292950],
      [0.00014613507, 4.73732166022, 3.93215326310],
      [0.00011162509, 5.82681796350, 224.34479570190],
      [0.00010997910, 0.48865004018, 138.51749687070],
      [0.00009527478, 2.95516862826, 35.16409022120],
      [0.00007545601, 5.23626582400, 109.94568878850],
      [0.00004220241, 3.23328220918, 70.84944530420],
      [0.00004051900, 2.27755017300, 151.04766984290],
      [0.00003354596, 1.06549007380, 4.45341812490],
      [0.00002926718, 4.62903718891, 9.56122755560],
      [0.00003490340, 5.48306144511, 146.59425171800],
      [0.00003144069, 4.75199570434, 77.75054398390],
      [0.00002922333, 5.35235361027, 85.82729883120],
      [0.00002272788, 4.36600400036, 70.32818044240],
      [0.00002051219, 1.51773566586, 0.11187458460],
      [0.00002148602, 0.60745949945, 38.13303563780],
      [0.00001991643, 4.92437588682, 277.03499374140],
      [0.00001376226, 2.04283539351, 65.22037101170],
      [0.00001666902, 3.62744066769, 380.12776796000],
      [0.00001284107, 3.11347961505, 202.25339517410],
      [0.00001150429, 0.93343589092, 3.18139373770],
      [0.00001533221, 2.58594681212, 52.69019803950],
      [0.00001281604, 0.54271272721, 222.86032299360],
      [0.00001372139, 4.19641530878, 111.43016149680],
      [0.00001221029, 0.19900650030, 108.46121608020],
      [0.00000946181, 1.19253165736, 127.47179660680],
      [0.00001150989, 4.17898916639, 33.67961751290]
    ],
    [
      [74.78159860910, 0.00000000000, 0.00000000000],
      [0.00154332863, 5.24158770553, 74.78159856730],
      [0.00024456474, 1.71260334156, 1.48447270830],
      [0.00009258442, 0.42829732350, 11.04570026390],
      [0.00008265977, 1.50218091379, 63.73589830340],
      [0.00009150160, 1.41213765216, 149.56319713460]
    ]
  ],
  [
    [
      [0.01346277648, 2.61877810547, 74.78159856730],
      [0.00062341400, 5.08111189648, 149.56319713460],
      [0.00061601196, 3.14159265359, 0.00000000000],
      [0.00009963722, 1.61603805646, 76.26607127560],
      [0.00009926160, 0.57630380333, 73.29712585900]
    ],
    [
      [0.00034101978, 0.01321929936, 74.78159856730]
    ]
  ],
  [
    [
      [19.21264847206, 0.00000000000, 0.00000000000],
      [0.88784984413, 5.60377527014, 74.78159856730],
      [0.03440836062, 0.32836099706, 73.29712585900],
      [0.02055653860, 1.78295159330, 149.56319713460],
      [0.00649322410, 4.52247285911, 76.26607127560],
      [0.00602247865, 3.86003823674, 63.73589830340],
      [0.00496404167, 1.40139935333, 454.90936652730],
      [0.00338525369, 1.58002770318, 138.51749687070],
      [0.00243509114, 1.57086606044, 71.81265315070],
      [0.00190522303, 1.99809394714, 1.48447270830],
      [0.00161858838, 2.79137786799, 148.07872442630],
      [0.00143706183, 1.38368544947, 11.04570026390],
      [0.00093192405, 0.17437220467, 36.64856292950],
      [0.00071424548, 4.24509236074, 224.34479570190],
      [0.00089806014, 3.66105364565, 109.94568878850],
      [0.00039009723, 1.66971401684, 70.84944530420],
      [0.00046677296, 1.39976401694, 35.16409022120],
      [0.00039025624, 3.36234773834, 277.03499374140],
      [0.00036755274, 3.88649278513, 146.59425171800],
      [0.00030348723, 0.70100838798, 151.04766984290],
      [0.00029156413, 3.18056336700, 77.75054398390]
    ],
    [
      [0.01479896629, 3.67205697578, 74.78159856730]
    ]
  ]
],

    # Neptune
    [
  [
    [
      [5.31188633046, 0.00000000000, 0.00000000000],
      [0.01798475530, 2.90101273890, 38.13303563780],
      [0.01019727652, 0.48580922867, 1.48447270830],
      [0.00124531845, 4.83008090676, 36.64856292950],
      [0.00042064466, 5.41054993053, 2.96894541660],
      [0.00037714584, 6.09221808686, 35.16409022120],
      [0.00033784738, 1.24488874087, 76.26607127560],
      [0.00016482741, 0.00007727998, 491.55792945680],
      [0.00009198584, 4.93747051954, 39.61750834610],
      [0.00008994250, 0.27462171806, 175.16605980020]
    ],
    [
      [38.13303563957, 0.00000000000, 0.00000000000],
      [0.00016604172, 4.86323329249, 1.48447270830],
      [0.00015744045, 2.27887427527, 38.13303563780]
    ]
  ],
  [
    [
      [0.03088622933, 1.44104372644, 38.13303563780],
      [0.00027780087, 5.91271884599, 76.26607127560],
      [0.00027623609, 0.00000000000, 0.00000000000],
      [0.00015355489, 2.52123799551, 36.64856292950],
      [0.00015448133, 3.50877079215, 39.61750834610]
    ]
  ],
  [
    [
      [30.07013205828, 0.00000000000, 0.00000000000],
      [0.27062259632, 1.32999459377, 38.13303563780],
      [0.01691764014, 3.25186135653, 36.64856292950],
      [0.00807830553, 5.18592878704, 1.48447270830],
      [0.00537760510, 4.52113935896, 35.16409022120],
      [0.00495725141, 1.57105641650, 491.55792945680],
      [0.00274571975, 1.84552258866, 175.16605980020]
    ]
  ]
],
]

def _CalcVsop(model, time):
    spher = []
    t = time.tt / 365250
    for formula in model:
        tpower = 1.0
        coord = 0.0
        for series in formula:
            coord += tpower * sum(term[0] * math.cos(term[1] + (t * term[2])) for term in series)
            tpower *= t
        spher.append(coord)

    # Convert spherical coordinates to ecliptic cartesian coordinates.
    r_coslat = spher[2] * math.cos(spher[1])
    ex = r_coslat * math.cos(spher[0])
    ey = r_coslat * math.sin(spher[0])
    ez = spher[2] * math.sin(spher[1])

    # Convert ecliptic cartesian coordinates to equatorial cartesian coordinates.
    vx = ex + 0.000000440360*ey - 0.000000190919*ez
    vy = -0.000000479966*ex + 0.917482137087*ey - 0.397776982902*ez
    vz = 0.397776982902*ey + 0.917482137087*ez
    return Vector(vx, vy, vz, time)

def _CalcEarth(time):
    return _CalcVsop(_vsop[BODY_EARTH], time)

# END VSOP
#----------------------------------------------------------------------------
# BEGIN CHEBYSHEV

_pluto = [
{ 'tt':-109573.500000, 'ndays':26141.000000, 'coeff':[
    [-30.303124711144, -18.980368465705, 3.206649343866],
    [20.092745278347, -27.533908687219, -14.641121965990],
    [9.137264744925, 6.513103657467, -0.720732357468],
    [-1.201554708717, 2.149917852301, 1.032022293526],
    [-0.566068170022, -0.285737361191, 0.081379987808],
    [0.041678527795, -0.143363105040, -0.057534475984],
    [0.041087908142, 0.007911321580, -0.010270655537],
    [0.001611769878, 0.011409821837, 0.003679980733],
    [-0.002536458296, -0.000145632543, 0.000949924030],
    [0.001167651969, -0.000049912680, 0.000115867710],
    [-0.000196953286, 0.000420406270, 0.000110147171],
    [0.001073825784, 0.000442658285, 0.000146985332],
    [-0.000906160087, 0.001702360394, 0.000758987924],
    [-0.001467464335, -0.000622191266, -0.000231866243],
    [-0.000008986691, 0.000004086384, 0.000001442956],
    [-0.001099078039, -0.000544633529, -0.000205534708],
    [0.001259974751, -0.002178533187, -0.000965315934],
    [0.001695288316, 0.000768480768, 0.000287916141],
    [-0.001428026702, 0.002707551594, 0.001195955756]]
},
{ 'tt':-83432.500000, 'ndays':26141.000000, 'coeff':[
    [67.049456204563, -9.279626603192, -23.091941092128],
    [14.860676672314, 26.594121136143, 3.819668867047],
    [-6.254409044120, 1.408757903538, 2.323726101433],
    [0.114416381092, -0.942273228585, -0.328566335886],
    [0.074973631246, 0.106749156044, 0.010806547171],
    [-0.018627741964, -0.009983491157, 0.002589955906],
    [0.006167206174, -0.001042430439, -0.001521881831],
    [-0.000471293617, 0.002337935239, 0.001060879763],
    [-0.000240627462, -0.001380351742, -0.000546042590],
    [0.001872140444, 0.000679876620, 0.000240384842],
    [-0.000334705177, 0.000693528330, 0.000301138309],
    [0.000796124758, 0.000653183163, 0.000259527079],
    [-0.001276116664, 0.001393959948, 0.000629574865],
    [-0.001235158458, -0.000889985319, -0.000351392687],
    [-0.000019881944, 0.000048339979, 0.000021342186],
    [-0.000987113745, -0.000748420747, -0.000296503569],
    [0.001721891782, -0.001893675502, -0.000854270937],
    [0.001505145187, 0.001081653337, 0.000426723640],
    [-0.002019479384, 0.002375617497, 0.001068258925]]
},
{ 'tt':-57291.500000, 'ndays':26141.000000, 'coeff':[
    [46.038290912405, 73.773759757856, 9.148670950706],
    [-22.354364534703, 10.217143138926, 9.921247676076],
    [-2.696282001399, -4.440843715929, -0.572373037840],
    [0.385475818800, -0.287872688575, -0.205914693555],
    [0.020994433095, 0.004256602589, -0.004817361041],
    [0.003212255378, 0.000574875698, -0.000764464370],
    [-0.000158619286, -0.001035559544, -0.000535612316],
    [0.000967952107, -0.000653111849, -0.000292019750],
    [0.001763494906, -0.000370815938, -0.000224698363],
    [0.001157990330, 0.001849810828, 0.000759641577],
    [-0.000883535516, 0.000384038162, 0.000191242192],
    [0.000709486562, 0.000655810827, 0.000265431131],
    [-0.001525810419, 0.001126870468, 0.000520202001],
    [-0.000983210860, -0.001116073455, -0.000456026382],
    [-0.000015655450, 0.000069184008, 0.000029796623],
    [-0.000815102021, -0.000900597010, -0.000365274209],
    [0.002090300438, -0.001536778673, -0.000709827438],
    [0.001234661297, 0.001342978436, 0.000545313112],
    [-0.002517963678, 0.001941826791, 0.000893859860]]
},
{ 'tt':-31150.500000, 'ndays':26141.000000, 'coeff':[
    [-39.074661990988, 30.963513412373, 21.431709298065],
    [-12.033639281924, -31.693679132310, -6.263961539568],
    [7.233936758611, -3.979157072767, -3.421027935569],
    [1.383182539917, 1.090729793400, -0.076771771448],
    [-0.009894394996, 0.313614402007, 0.101180677344],
    [-0.055459383449, 0.031782406403, 0.026374448864],
    [-0.011074105991, -0.007176759494, 0.001896208351],
    [-0.000263363398, -0.001145329444, 0.000215471838],
    [0.000405700185, -0.000839229891, -0.000418571366],
    [0.001004921401, 0.001135118493, 0.000406734549],
    [-0.000473938695, 0.000282751002, 0.000114911593],
    [0.000528685886, 0.000966635293, 0.000401955197],
    [-0.001838869845, 0.000806432189, 0.000394594478],
    [-0.000713122169, -0.001334810971, -0.000554511235],
    [0.000006449359, 0.000060730000, 0.000024513230],
    [-0.000596025142, -0.000999492770, -0.000413930406],
    [0.002364904429, -0.001099236865, -0.000528480902],
    [0.000907458104, 0.001537243912, 0.000637001965],
    [-0.002909908764, 0.001413648354, 0.000677030924]]
},
{ 'tt':-5009.500000, 'ndays':26141.000000, 'coeff':[
    [23.380075041204, -38.969338804442, -19.204762094135],
    [33.437140696536, 8.735194448531, -7.348352917314],
    [-3.127251304544, 8.324311848708, 3.540122328502],
    [-1.491354030154, -1.350371407475, 0.028214278544],
    [0.361398480996, -0.118420687058, -0.145375605480],
    [-0.011771350229, 0.085880588309, 0.030665997197],
    [-0.015839541688, -0.014165128211, 0.000523465951],
    [0.004213218926, -0.001426373728, -0.001906412496],
    [0.001465150002, 0.000451513538, 0.000081936194],
    [0.000640069511, 0.001886692235, 0.000884675556],
    [-0.000883554940, 0.000301907356, 0.000127310183],
    [0.000245524038, 0.000910362686, 0.000385555148],
    [-0.001942010476, 0.000438682280, 0.000237124027],
    [-0.000425455660, -0.001442138768, -0.000607751390],
    [0.000004168433, 0.000033856562, 0.000013881811],
    [-0.000337920193, -0.001074290356, -0.000452503056],
    [0.002544755354, -0.000620356219, -0.000327246228],
    [0.000534534110, 0.001670320887, 0.000702775941],
    [-0.003169380270, 0.000816186705, 0.000427213817]]
},
{ 'tt':21131.500000, 'ndays':26141.000000, 'coeff':[
    [74.130449310804, 43.372111541004, -8.799489207171],
    [-8.705941488523, 23.344631690845, 9.908006472122],
    [-4.614752911564, -2.587334376729, 0.583321715294],
    [0.316219286624, -0.395448970181, -0.219217574801],
    [0.004593734664, 0.027528474371, 0.007736197280],
    [-0.001192268851, -0.004987723997, -0.001599399192],
    [0.003051998429, -0.001287028653, -0.000780744058],
    [0.001482572043, 0.001613554244, 0.000635747068],
    [0.000581965277, 0.000788286674, 0.000315285159],
    [-0.000311830730, 0.001622369930, 0.000714817617],
    [-0.000711275723, -0.000160014561, -0.000050445901],
    [0.000177159088, 0.001032713853, 0.000435835541],
    [-0.002032280820, 0.000144281331, 0.000111910344],
    [-0.000148463759, -0.001495212309, -0.000635892081],
    [-0.000009629403, -0.000013678407, -0.000006187457],
    [-0.000061196084, -0.001119783520, -0.000479221572],
    [0.002630993795, -0.000113042927, -0.000112115452],
    [0.000132867113, 0.001741417484, 0.000743224630],
    [-0.003293498893, 0.000182437998, 0.000158073228]]
},
{ 'tt':47272.500000, 'ndays':26141.000000, 'coeff':[
    [-5.727994625506, 71.194823351703, 23.946198176031],
    [-26.767323214686, -12.264949302780, 4.238297122007],
    [0.890596204250, -5.970227904551, -2.131444078785],
    [0.808383708156, -0.143104108476, -0.288102517987],
    [0.089303327519, 0.049290470655, -0.010970501667],
    [0.010197195705, 0.012879721400, 0.001317586740],
    [0.001795282629, 0.004482403780, 0.001563326157],
    [-0.001974716105, 0.001278073933, 0.000652735133],
    [0.000906544715, -0.000805502229, -0.000336200833],
    [0.000283816745, 0.001799099064, 0.000756827653],
    [-0.000784971304, 0.000123081220, 0.000068812133],
    [-0.000237033406, 0.000980100466, 0.000427758498],
    [-0.001976846386, -0.000280421081, -0.000072417045],
    [0.000195628511, -0.001446079585, -0.000624011074],
    [-0.000044622337, -0.000035865046, -0.000013581236],
    [0.000204397832, -0.001127474894, -0.000488668673],
    [0.002625373003, 0.000389300123, 0.000102756139],
    [-0.000277321614, 0.001732818354, 0.000749576471],
    [-0.003280537764, -0.000457571669, -0.000116383655]]
}]

def _ChebScale(t_min, t_max, t):
    return (2*t - (t_max + t_min)) / (t_max - t_min)

def _CalcChebyshev(model, time):
    # Search for a record that overlaps the given time value.
    for record in model:
        x = _ChebScale(record['tt'], record['tt'] + record['ndays'], time.tt)
        if -1 <= x <= +1:
            coeff = record['coeff']
            pos = []
            for d in range(3):
                p0 = 1
                sum = coeff[0][d]
                p1 = x
                sum += coeff[1][d] * p1
                for k in range(2, len(coeff)):
                    p2 = (2 * x * p1) - p0
                    sum += coeff[k][d] * p2
                    p0 = p1
                    p1 = p2
                pos.append(sum - coeff[0][d]/2)
            return Vector(pos[0], pos[1], pos[2], time)
    raise Error('Cannot extrapolate Chebyshev model for given Terrestrial Time: {}'.format(time.tt))

# END CHEBYSHEV
#----------------------------------------------------------------------------
# BEGIN Search

def _QuadInterp(tm, dt, fa, fm, fb):
    Q = (fb + fa)/2 - fm
    R = (fb - fa)/2
    S = fm

    if Q == 0:
        # This is a line, not a parabola.
        if R == 0:
            # This is a HORIZONTAL line... can't make progress!
            return None
        x = -S / R
        if not (-1 <= x <= +1):
            return None  # out of bounds
    else:
        # It really is a parabola. Find roots x1, x2.
        u = R*R - 4*Q*S
        if u <= 0:
            return None
        ru = math.sqrt(u)
        x1 = (-R + ru) / (2 * Q)
        x2 = (-R - ru) / (2 * Q)

        if -1 <= x1 <= +1:
            if -1 <= x2 <= +1:
                # Two solutions... so parabola intersects twice.
                return None
            x = x1
        elif -1 <= x2 <= +1:
            x = x2
        else:
            return None

    t = tm + x*dt
    df_dt = (2*Q*x + R) / dt
    return (x, t, df_dt)

def Search(func, context, t1, t2, dt_tolerance_seconds):
    dt_days = abs(dt_tolerance_seconds / _SECONDS_PER_DAY)
    f1 = func(context, t1)
    f2 = func(context, t2)
    iter = 0
    iter_limit = 20
    calc_fmid = True
    while True:
        iter += 1
        if iter > iter_limit:
            raise Error('Excessive iteration in Search')

        dt = (t2.tt - t1.tt) / 2.0
        tmid = t1.AddDays(dt)
        if abs(dt) < dt_days:
            # We are close enough to the event to stop the search.
            return tmid

        if calc_fmid:
            fmid = func(context, tmid)
        else:
            # We already have the correct value of fmid from the previous loop.
            calc_fmid = True

        # Quadratic interpolation:
        # Try to find a parabola that passes through the 3 points we have sampled:
        # (t1,f1), (tmid,fmid), (t2,f2).
        q = _QuadInterp(tmid.ut, t2.ut - tmid.ut, f1, fmid, f2)
        if q:
            (q_x, q_ut, q_df_dt) = q
            tq = Time(q_ut)
            fq = func(context, tq)
            if q_df_dt != 0.0:
                dt_guess = abs(fq / q_df_dt)
                if dt_guess < dt_days:
                    # The estimated time error is small enough that we can quit now.
                    return tq

                # Try guessing a tighter boundary with the interpolated root at the center.
                dt_guess *= 1.2
                if dt_guess < dt / 10.0:
                    tleft = tq.AddDays(-dt_guess)
                    tright = tq.AddDays(+dt_guess)
                    if (tleft.ut - t1.ut)*(tleft.ut - t2.ut) < 0.0:
                        if (tright.ut - t1.ut)*(tright.ut - t2.ut) < 0.0:
                            fleft = func(context, tleft)
                            fright = func(context, tright)
                            if fleft < 0.0 and fright >= 0.0:
                                f1 = fleft
                                f2 = fright
                                t1 = tleft
                                t2 = tright
                                fmid = fq
                                calc_fmid = False
                                continue

        # Quadratic interpolation attempt did not work out.
        # Just divide the region in two parts and pick whichever one appears to contain a root.
        if f1 < 0.0 and fmid >= 0.0:
            t2 = tmid
            f2 = fmid
            continue

        if fmid < 0.0 and f2 >= 0.0:
            t1 = tmid
            f1 = fmid
            continue

        # Either there is no ascending zero-crossing in this range
        # or the search window is too wide (more than one zero-crossing).
        return None

# END Search
#----------------------------------------------------------------------------

def HelioVector(body, time):
    if body == BODY_PLUTO:
        return _CalcChebyshev(_pluto, time)

    if 0 <= body <= len(_vsop):
        return _CalcVsop(_vsop[body], time)

    if body == BODY_SUN:
        return Vector(0.0, 0.0, 0.0, time)

    if body == BODY_MOON:
        e = _CalcEarth(time)
        m = GeoMoon(time)
        return Vector(e.x+m.x, e.y+m.y, e.z+m.z, time)

    raise InvalidBodyError()


def GeoVector(body, time, aberration):
    if body == BODY_MOON:
        return GeoMoon(time)

    if body == BODY_EARTH:
        return Vector(0.0, 0.0, 0.0, time)

    if not aberration:
        # No aberration, so calculate Earth's position once, at the time of observation.
        earth = _CalcEarth(time)

    # Correct for light-travel time, to get position of body as seen from Earth's center.
    ltime = time
    for iter in range(10):
        h = HelioVector(body, ltime)
        if aberration:
            # Include aberration, so make a good first-order approximation
            # by backdating the Earth's position also.
            # This is confusing, but it works for objects within the Solar System
            # because the distance the Earth moves in that small amount of light
            # travel time (a few minutes to a few hours) is well approximated
            # by a line segment that substends the angle seen from the remote
            # body viewing Earth. That angle is pretty close to the aberration
            # angle of the moving Earth viewing the remote body.
            # In other words, both of the following approximate the aberration angle:
            #    (transverse distance Earth moves) / (distance to body)
            #    (transverse speed of Earth) / (speed of light).
            earth = _CalcEarth(ltime)

        geo = Vector(h.x-earth.x, h.y-earth.y, h.z-earth.z, time)
        if body == BODY_SUN:
            # The Sun's heliocentric coordinates are always (0,0,0). No need to correct.
            return geo

        ltime2 = time.AddDays(-geo.Length() / _C_AUDAY)
        dt = abs(ltime2.tt - ltime.tt)
        if dt < 1.0e-9:
            return geo

        ltime = ltime2

    raise Error('Light-travel time solver did not converge: dt={}'.format(dt))


def Equator(body, time, observer, ofdate, aberration):
    gc_observer = _geo_pos(time, observer)
    gc = GeoVector(body, time, aberration)
    j2000 = [
        gc.x - gc_observer[0],
        gc.y - gc_observer[1],
        gc.z - gc_observer[2]
    ]
    if not ofdate:
        return _vector2radec(j2000)
    temp = _precession(0, j2000, time.tt)
    datevect = _nutation(time, 0, temp)
    return _vector2radec(datevect)

REFRACTION_NONE = 0
REFRACTION_NORMAL = 1
REFRACTION_JPLHOR = 2

class HorizontalCoordinates:
    def __init__(self, azimuth, altitude, ra, dec):
        self.azimuth = azimuth
        self.altitude = altitude
        self.ra = ra
        self.dec = dec

def Horizon(time, observer, ra, dec, refraction):
    if not (REFRACTION_NONE <= refraction <= REFRACTION_JPLHOR):
        raise Error('Invalid refraction type: ' + str(refraction))

    sinlat = math.sin(observer.latitude * _DEG2RAD)
    coslat = math.cos(observer.latitude * _DEG2RAD)
    sinlon = math.sin(observer.longitude * _DEG2RAD)
    coslon = math.cos(observer.longitude * _DEG2RAD)
    sindc = math.sin(dec * _DEG2RAD)
    cosdc = math.cos(dec * _DEG2RAD)
    sinra = math.sin(ra * 15 * _DEG2RAD)
    cosra = math.cos(ra * 15 * _DEG2RAD)

    uze = [coslat*coslon, coslat*sinlon, sinlat]
    une = [-sinlat*coslon, -sinlat*sinlon, coslat]
    uwe = [sinlon, -coslon, 0.0]

    angle = -15.0 * _sidereal_time(time)
    uz = _spin(angle, uze)
    un = _spin(angle, une)
    uw = _spin(angle, uwe)

    p = [cosdc*cosra, cosdc*sinra, sindc]

    pz = p[0]*uz[0] + p[1]*uz[1] + p[2]*uz[2]
    pn = p[0]*un[0] + p[1]*un[1] + p[2]*un[2]
    pw = p[0]*uw[0] + p[1]*uw[1] + p[2]*uw[2]

    proj = math.sqrt(pn*pn + pw*pw)
    az = 0.0
    if proj > 0.0:
        az = -math.atan2(pw, pn) * _RAD2DEG
        if az < 0:
            az += 360
        if az >= 360:
            az -= 360
    zd = math.atan2(proj, pz) * _RAD2DEG
    hor_ra = ra
    hor_dec = dec

    if refraction != REFRACTION_NONE:
        zd0 = zd

        # http://extras.springer.com/1999/978-1-4471-0555-8/chap4/horizons/horizons.pdf
        # JPL Horizons says it uses refraction algorithm from
        # Meeus "Astronomical Algorithms", 1991, p. 101-102.
        # I found the following Go implementation:
        # https://github.com/soniakeys/meeus/blob/master/v3/refraction/refract.go
        # This is a translation from the function "Saemundsson" there.
        # I found experimentally that JPL Horizons clamps the angle to 1 degree below the horizon.
        # This is important because the 'refr' formula below goes crazy near hd = -5.11.
        hd = 90.0 - zd
        if hd < -1.0:
            hd = -1.0

        refr = (1.02 / math.tan((hd+10.3/(hd+5.11))*_DEG2RAD)) / 60.0

        if refraction == REFRACTION_NORMAL and zd > 91.0:
            # In "normal" mode we gradually reduce refraction toward the nadir
            # so that we never get an altitude angle less than -90 degrees.
            # When horizon angle is -1 degrees, zd = 91, and the factor is exactly 1.
            # As zd approaches 180 (the nadir), the fraction approaches 0 linearly.
            refr *= (180.0 - zd) / 89.0

        zd -= refr

        if refr > 0.0 and zd > 3.0e-4:
            sinzd = math.sin(zd * _DEG2RAD)
            coszd = math.cos(zd * _DEG2RAD)
            sinzd0 = math.sin(zd0 * _DEG2RAD)
            coszd0 = math.cos(zd0 * _DEG2RAD)

            pr = [(((p[j] - coszd0 * uz[j]) / sinzd0)*sinzd + uz[j]*coszd) for j in range(3)]
            proj = math.sqrt(pr[0]*pr[0] + pr[1]*pr[1])
            if proj > 0:
                hor_ra = math.atan2(pr[1], pr[0]) * _RAD2DEG / 15
                if hor_ra < 0:
                    hor_ra += 24
                if hor_ra >= 24:
                    hor_ra -= 24
            else:
                hor_ra = 0
            hor_dec = math.atan2(pr[2], proj) * _RAD2DEG

    return HorizontalCoordinates(az, 90.0 - zd, hor_ra, hor_dec)

class EclipticCoordinates:
    def __init__(self, ex, ey, ez, elat, elon):
        self.ex = ex
        self.ey = ey
        self.ez = ez
        self.elat = elat
        self.elon = elon

def _RotateEquatorialToEcliptic(pos, obliq_radians):
    cos_ob = math.cos(obliq_radians)
    sin_ob = math.sin(obliq_radians)
    ex = +pos[0]
    ey = +pos[1]*cos_ob + pos[2]*sin_ob
    ez = -pos[1]*sin_ob + pos[2]*cos_ob
    xyproj = math.sqrt(ex*ex + ey*ey)
    if xyproj > 0.0:
        elon = _RAD2DEG * math.atan(ey, ex)
        if elon < 0.0:
            elon += 360.0
    else:
        elon = 0.0
    elat = _RAD2DEG * math.atan(ez, xyproj)
    return EclipticCoordinates(ex, ey, ez, elat, elon)

def SunPosition(time):
    # Correct for light travel time from the Sun.
    # Otherwise season calculations (equinox, solstice) will all be early by about 8 minutes!
    adjusted_time = time.AddDays(-1.0 / _C_AUDAY)
    earth2000 = CalcEarth(adjusted_time)
    sun2000 = [-earth2000.x, -earth2000.y, -earth2000.z]

    # Convert to equatorial Cartesian coordinates of date.
    stemp = _precession(0.0, sun2000, adjusted_time.tt)
    sun_ofdate = _nutation(adjusted_time, 0, stemp)

    # Convert equatorial coordinates to ecliptic coordinates.
    true_obliq = _DEG2RAD * adjusted_time._etilt().tobl
    return RotateEquatorialToEcliptic(sun_ofdate, true_obliq)

def Ecliptic(equ):
    # Based on NOVAS functions equ2ecl() and equ2ecl_vec().
    ob2000 = 0.40909260059599012   # mean obliquity of the J2000 ecliptic in radians
    return RotateEquatorialToEcliptic([equ.x, equ.y, equ.z], ob2000)

def EclipticLongitude(body, time):
    if body == BODY_SUN:
        raise InvalidBodyError()
    hv = HelioVector(body, time)
    eclip = Ecliptic(hv)
    return eclip.elon

def AngleFromSun(body, time):
    if body == EARTH:
        raise EarthNotAllowedError()
    sv = GeoVector(BODY_SUN, time, True)
    bv = GeoVector(body, time, True)
    return _AngleBetween(sv, bv)

def LongitudeFromSun(body, time):
    if body == EARTH:
        raise EarthNotAllowedError()
    sv = GeoVector(BODY_SUN, time, True)
    se = Ecliptic(sv)
    bv = GeoVector(body, time, True)
    be = Ecliptic(bv)
    return _NormalizeLongitude(be.elon - se.elon)

class ElongationEvent:
    def __init__(self, time, visibility, elongation, ecliptic_separation):
        self.time = time
        self.visibility = visibility
        self.elongation = elongation
        self.ecliptic_separation = ecliptic_separation

def Elongation(body, time):
    angle = LongitudeFromSun(body, time)
    if angle > 180.0:
        visibility = 'morning'
        esep = 360.0 - angle
    else:
        visibility = 'evening'
        esep = angle
    angle = AngleFromSun(body, time)
    return ElongationEvent(time, visibility, angle, esep)

def _rlon_offset(body, time, direction, targetRelLon):
    plon = EclipticLongitude(body, time)
    elon = EclipticLongitude(BODY_EARTH, time)
    diff = direction * (elon - plon)
    return _LongitudeOffset(diff - targetRelLon)

def SearchRelativeLongitude(body, targetRelLon, startTime):
    if body == BODY_EARTH:
        raise EarthNotAllowedError()
    if body == BODY_MOON or body == BODY_SUN:
        raise InvalidBodyError()
    syn = _SynodicPeriod(body)
    direction = +1 if _IsSuperiorPlanet(body) else -1
    # Iterate until we converge on the desired event.
    # Calculate the error angle, which will be a negative number of degrees,
    # meaning we are "behind" the target relative longitude.
    error_angle = _rlon_offset(body, startTime, direction, targetRelLon)
    if error_angle > 0.0:
        error_angle -= 360.0    # force searching forward in time
    time = startTime
    iter = 0
    while iter < 100:
        # Estimate how many days in the future (positive) or past (negative)
        # we have to go to get closer to the target relative longitude.
        day_adjust = (-error_angle/360.0) * syn
        time = time.AddDays(day_adjust)
        if abs(day_adjust) * _SECONDS_PER_DAY < 1.0:
            return time
        prev_angle = error_angle
        error_angle = _rlon_offset(body, time, direction, targetRelLon)
        if abs(prev_angle) < 30.0 and prev_angle != error_angle:
            # Improve convergence for Mercury/Mars (eccentric orbits)
            # by adjusting the synodic period to more closely match the
            # variable speed of both planets in this part of their respective orbits.
            ratio = prev_angle / (prev_angle - error_angle)
            if 0.5 < ratio < 2.0:
                syn *= ratio
        iter += 1
    raise NoConvergeError()

def _neg_elong_slope(body, time):
    dt = 0.1
    t1 = time.AddDays(-dt/2.0)
    t2 = time.AddDays(+dt/2.0)
    e1 = AngleFromSun(body, t1)
    e2 = AngleFromSun(body, t2)
    return (e1 - e2)/dt

def SearchMaxElongation(body, startTime):
    if body == BODY_MERCURY:
        s1 = 50.0
        s2 = 85.0
    elif body == BODY_VENUS:
        s1 = 40.0
        s2 = 50.0
    else:
        raise InvalidBodyError()
    syn = _SynodicPeriod(body)
    iter = 1
    while iter <= 2:
        plon = EclipticLongitude(body, startTime)
        elon = EclipticLongitude(BODY_EARTH, startTime)
        rlon = _LongitudeOffset(plon - elon)    # clamp to (-180, +180]

        # The slope function is not well-behaved when rlon is near 0 degrees or 180 degrees
        # because there is a cusp there that causes a discontinuity in the derivative.
        # So we need to guard against searching near such times.
        if rlon >= -s1 and rlon < +s1:
            # Seek to the window [+s1, +s2].
            adjust_days = 0.0
            # Search forward for the time t1 when rel lon = +s1.
            rlon_lo = +s1
            # Search forward for the time t2 when rel lon = +s2.
            rlon_hi = +s2
        elif rlon > +s2 or rlon < -s2:
            # Seek to the next search window at [-s2, -s1].
            adjust_days = 0.0
            # Search forward for the time t1 when rel lon = -s2.
            rlon_lo = -s2
            # Search forward for the time t2 when rel lon = -s1.
            rlon_hi = -s1
        elif rlon >= 0.0:
            # rlon must be in the middle of the window [+s1, +s2].
            # Search BACKWARD for the time t1 when rel lon = +s1.
            adjust_days = -syn / 4.0
            rlon_lo = +s1
            rlon_hi = +s2
            # Search forward from t1 to find t2 such that rel lon = +s2.
        else:
            # rlon must be in the middle of the window [-s2, -s1].
            # Search BACKWARD for the time t1 when rel lon = -s2.
            adjust_days = -syn / 4.0
            rlon_lo = -s2
            # Search forward from t1 to find t2 such that rel lon = -s1.
            rlon_hi = -s1

        t_start = startTime.AddDays(adjust_days)
        search1 = SearchRelativeLongitude(body, rlon_lo, t_start)
        if not search1:
            return None
        t1 = search1.time

        search2 = SearchRelativeLongitude(body, rlon_hi, t1)
        if not search2:
            return None
        t2 = search2.time

        # Now we have a time range [t1,t2] that brackets a maximum elongation event.
        # Confirm the bracketing.
        m1 = _neg_elong_slope(body, t1)
        if m1 >= 0.0:
            raise InternalError()   # there is a bug in the bracketing algorithm!

        m2 = _neg_elong_slope(body, t2)
        if m2 <= 0.0:
            raise InternalError()   # there is a bug in the bracketing algorithm!

        # Use the generic search algorithm to home in on where the slope crosses from negative to positive.
        searchx = Search(neg_elong_slope, body, t1, t2, 10.0)
        if not searchx:
            return None

        if searchx.time.tt >= startTime.tt:
            return Elongation(body, searchx.time)

        # This event is in the past (earlier than startTime).
        # We need to search forward from t2 to find the next possible window.
        # We never need to search more than twice.
        startTime = t2.AddDays(1.0)
        iter += 1


def _sun_offset(targetLon, time):
    ecl = SunPosition(time)
    return _LongitudeOffset(ecl.elon - targetLon)

def SearchSunLongitude(targetLon, startTime, limitDays):
    t2 = startTime.Add(limitDays)
    return Search(_sun_offset, targetLon, startTime, t2, 1.0)

def MoonPhase(time):
    return LongitudeFromSun(BODY_MOON, time)

def _moon_offset(targetLon, time):
    angle = MoonPhase(time)
    return _LongitudeOffset(angle - targetLon)

def SearchMoonPhase(targetLon, startTime, limitDays):
    # To avoid discontinuities in the _moon_offset function causing problems,
    # we need to approximate when that function will next return 0.
    # We probe it with the start time and take advantage of the fact
    # that every lunar phase repeats roughly every 29.5 days.
    # There is a surprising uncertainty in the quarter timing,
    # due to the eccentricity of the moon's orbit.
    # I have seen up to 0.826 days away from the simple prediction.
    # To be safe, we take the predicted time of the event and search
    # +/-0.9 days around it (a 1.8-day wide window).
    # But we must return None if the final result goes beyond limitDays after startTime.
    uncertainty = 0.9
    ya = _moon_offset(targetLon, startTime)
    if ya > 0.0:
        ya -= 360.0     # force searching forward in time, not backward
    est_dt = -(_MEAN_SYNODIC_MONTH * ya) / 360.0
    dt1 = est_dt - uncertainty
    if dt1 > limitDays:
        return None     # not possible for moon phase to occur within the specified window
    dt2 = min(limitDays, est_dt + uncertainty)
    t1 = startTime.AddDays(dt1)
    t2 = startTime.AddDays(dt2)
    return Search(_moon_offset, targetLon, t1, t2, 1.0)


#==================================================================================================
# + SearchSunLongitude
#       + _sun_offset
#       + SunPosition
#           + RotateEquatorialToEcliptic
# + Ecliptic
# + EclipticLongitude
# + AngleFromSun
# + SearchMaxElongation
#       + _neg_elong_slope
#       + SearchRelativeLongitude
#       + Elongation
#           + LongitudeFromSun
# + MoonPhase
# + SearchMoonPhase
#       + _moon_offset
# - SearchMoonQuarter
# - NextMoonQuarter
# - SearchHourAngle
# - SearchRiseSet
# - Seasons
# - Illumination
# - SearchPeakMagnitude
# - SearchLunarApsis
# - NextLunarApsis