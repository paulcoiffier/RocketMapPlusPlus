#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import json
import logging
import random
import time
import socket
import struct
import hashlib
import psutil
import subprocess
import requests
import configargparse
from datetime import datetime

from s2sphere import CellId, LatLng
from geopy.geocoders import GoogleV3
from requests_futures.sessions import FuturesSession
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from cHaversine import haversine
from pprint import pformat
from time import strftime
from timeit import default_timer

from protos.pogoprotos.enums.pokemon_id_pb2 import _POKEMONID

log = logging.getLogger(__name__)


def parse_unicode(bytestring):
    decoded_string = bytestring.decode(sys.getfilesystemencoding())
    return decoded_string


def memoize(function):
    memo = {}

    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper


@memoize
def get_args():
    # Pre-check to see if the -cf or --config flag is used on the command line.
    # If not, we'll use the env var or default value. This prevents layering of
    # config files as well as a missing config.ini.
    defaultconfigfiles = []
    if '-cf' not in sys.argv and '--config' not in sys.argv:
        defaultconfigfiles = [os.getenv('POGOMAP_CONFIG', os.path.join(
            os.path.dirname(__file__), '../config/config.ini'))]
    parser = configargparse.ArgParser(
        default_config_files=defaultconfigfiles,
        auto_env_var_prefix='POGOMAP_')
    parser.add_argument('-cf', '--config',
                        is_config_file=True, help='Set configuration file')
    parser.add_argument('-scf', '--shared-config',
                        is_config_file=True, help='Set a shared config')
    parser.add_argument('-l', '--location', type=parse_unicode,
                        help='Location, can be an address or coordinates.')
    # Default based on the average elevation of cities around the world.
    # Source: https://www.wikiwand.com/en/List_of_cities_by_elevation
    parser.add_argument('-alt', '--altitude',
                        help='Default altitude in meters.',
                        type=int, default=507)
    parser.add_argument('-altv', '--altitude-variance',
                        help='Variance for --altitude in meters',
                        type=int, default=1)
    parser.add_argument('-uac', '--use-altitude-cache',
                        help=('Query the Elevation API for each step,' +
                              ' rather than only once, and store results in' +
                              ' the database.'),
                        action='store_true', default=False)
    parser.add_argument('-al', '--access-logs',
                        help=("Write web logs to access.log."),
                        action='store_true', default=False)
    parser.add_argument('-ignf', '--ignorelist-file',
                        default='', help='File containing a list of ' +
                        'Pokemon IDs to ignore, one line per ID. ' +
                        'Spawnpoints will be saved, but ignored ' +
                        'Pokemon won\'t be encountered, sent to ' +
                        'webhooks or saved to the DB.')
    parser.add_argument('-nostore', '--no-api-store',
                        help=("Don't store the API objects used by the high"
                              + ' level accounts in memory. This will increase'
                              + ' the number of logins per account, but '
                              + ' decreases memory usage.'),
                        action='store_true', default=False)
    parser.add_argument('-apir', '--api-retries',
                        help=('Number of times to retry an API request.'),
                        type=int, default=3)
    webhook_list = parser.add_mutually_exclusive_group()
    webhook_list.add_argument('-wwht', '--webhook-whitelist',
                              action='append', default=[],
                              help=('List of Pokemon to send to '
                                    'webhooks. Specified as Pokemon ID.'))
    webhook_list.add_argument('-wblk', '--webhook-blacklist',
                              action='append', default=[],
                              help=('List of Pokemon NOT to send to '
                                    'webhooks. Specified as Pokemon ID.'))
    webhook_list.add_argument('-wwhtf', '--webhook-whitelist-file',
                              default='', help='File containing a list of '
                                               'Pokemon IDs to be sent to '
                                               'webhooks.')
    webhook_list.add_argument('-wblkf', '--webhook-blacklist-file',
                              default='', help='File containing a list of '
                                               'Pokemon IDs NOT to be sent to'
                                               'webhooks.')
    parser.add_argument('-ld', '--login-delay',
                        help='Time delay between each login attempt.',
                        type=float, default=6)
    parser.add_argument('-lr', '--login-retries',
                        help=('Number of times to retry the login before ' +
                              'refreshing a thread.'),
                        type=int, default=3)
    parser.add_argument('-mf', '--max-failures',
                        help=('Maximum number of failures to parse ' +
                              'locations before an account will go into a ' +
                              'sleep for -ari/--account-rest-interval ' +
                              'seconds.'),
                        type=int, default=5)
    parser.add_argument('-me', '--max-empty',
                        help=('Maximum number of empty scans before an ' +
                              'account will go into a sleep for ' +
                              '-ari/--account-rest-interval seconds.' +
                              'Reasonable to use with proxies.'),
                        type=int, default=0)
    parser.add_argument('-bsr', '--bad-scan-retry',
                        help=('Number of bad scans before giving up on a ' +
                              'step. Default 2, 0 to disable.'),
                        type=int, default=2)
    parser.add_argument('-msl', '--min-seconds-left',
                        help=('Time that must be left on a spawn before ' +
                              'considering it too late and skipping it. ' +
                              'For example 600 would skip anything with ' +
                              '< 10 minutes remaining. Default 0.'),
                        type=int, default=0)
    parser.add_argument('-dc', '--display-in-console',
                        help='Display Found Pokemon in Console.',
                        action='store_true', default=False)
    parser.add_argument('-H', '--host', help='Set web server listening host.',
                        default='127.0.0.1')
    parser.add_argument('-P', '--port', type=int,
                        help='Set web server listening port.', default=5000)
    parser.add_argument('-L', '--locale',
                        help=('Locale for Pokemon names (check' +
                              ' static/dist/locales for more).'),
                        default='en')
    parser.add_argument('-eh', '--external-hostname',
                        help='Hostname used for external requests.',
                        default="http://127.0.0.1:5000")
    parser.add_argument('-c', '--china',
                        help='Coordinates transformer for China.',
                        action='store_true')
    parser.add_argument('-k', '--gmaps-key',
                        help='Google Maps Javascript API Key.',
                        required=True)
    parser.add_argument('--skip-empty',
                        help=('Enables skipping of empty cells in normal ' +
                              'scans - requires previously populated ' +
                              'database (not to be used with -ss)'),
                        action='store_true', default=False)
    parser.add_argument('-C', '--cors', help='Enable CORS on web server.',
                        action='store_true', default=False)
    parser.add_argument('-cd', '--clear-db',
                        help=('Deletes the existing database before ' +
                              'starting the Webserver.'),
                        action='store_true', default=False)
    parser.add_argument('-np', '--no-pokemon',
                        help=('Disables Pokemon from the map (including ' +
                              'parsing them into local db.)'),
                        action='store_true', default=False)
    parser.add_argument('-ng', '--no-gyms',
                        help=('Disables Gyms from the map (including ' +
                              'parsing them into local db).'),
                        action='store_true', default=False)
    parser.add_argument('-nr', '--no-raids',
                        help=('Disables Raids from the map (including ' +
                              'parsing them into local db).'),
                        action='store_true', default=False)
    parser.add_argument('-nk', '--no-pokestops',
                        help=('Disables PokeStops from the map (including ' +
                              'parsing them into local db).'),
                        action='store_true', default=False)
    parser.add_argument('-ssct', '--ss-cluster-time',
                        help=('Time threshold in seconds for spawn point ' +
                              'clustering (0 to disable).'),
                        type=int, default=0)
    parser.add_argument('-ldur', '--lure-duration',
                        help=('Change duration for lures set on pokestops. ' +
                              'This is useful for events that extend lure ' +
                              'duration.'), type=int, default=30)
    parser.add_argument('-px', '--proxy',
                        help='Proxy url (e.g. socks5://127.0.0.1:9050)',
                        action='append')
    parser.add_argument('-pxsc', '--proxy-skip-check',
                        help='Disable checking of proxies before start.',
                        action='store_true', default=False)
    parser.add_argument('-pxt', '--proxy-test-timeout',
                        help='Timeout settings for proxy checker in seconds.',
                        type=int, default=5)
    parser.add_argument('-pxre', '--proxy-test-retries',
                        help=('Number of times to retry sending proxy ' +
                              'test requests on failure.'),
                        type=int, default=0)
    parser.add_argument('-pxbf', '--proxy-test-backoff-factor',
                        help=('Factor (in seconds) by which the delay ' +
                              'until next retry will increase.'),
                        type=float, default=0.25)
    parser.add_argument('-pxc', '--proxy-test-concurrency',
                        help=('Async requests pool size.'), type=int,
                        default=0)
    parser.add_argument('-pxd', '--proxy-display',
                        help=('Display info on which proxy being used ' +
                              '(index or full). To be used with -ps.'),
                        type=str, default='index')
    parser.add_argument('-pxf', '--proxy-file',
                        help=('Load proxy list from text file (one proxy ' +
                              'per line), overrides -px/--proxy.'))
    parser.add_argument('-pxr', '--proxy-refresh',
                        help=('Period of proxy file reloading, in seconds. ' +
                              'Works only with -pxf/--proxy-file. ' +
                              '(0 to disable).'),
                        type=int, default=0)
    parser.add_argument('-pxo', '--proxy-rotation',
                        help=('Enable proxy rotation with account changing ' +
                              'for search threads (none/round/random).'),
                        type=str, default='round')
    parser.add_argument('-sts', '--stepsize',
                        help=('Size of the steps'),
                        type=float, default=0.00007)
    parser.add_argument('-mr', '--maxradius',
                        help=('Maximum radius (in km), use 0 to disable'),
                        type=int, default=0)
    parser.add_argument('-st', '--scheduletimeout',
                        help=('Timeout in minutes before resetting scheduled route for fetch'),
                        type=int, default=10)
    parser.add_argument('-dmm', '--dont-move-map',
                        help=("Don't update the map location on new scan location"),
                        action='store_true', default=False)
    parser.add_argument('-tf', '--teleport-factor',
                        help=('Teleport factor for the stepsize'),
                        type=float, default=10)
    parser.add_argument('-ti', '--teleport-interval',
                        help=('Time between teleports in seconds'),
                        type=int, default=60)
    parser.add_argument('-tig', '--teleport-ignore',
                        help=('Ignore coordinates inside this radius for teleport scheduling'),
                        type=int, default=300)
    parser.add_argument('-qed', '--quest-expiration-days',
                        help=('Number of days before quest info expires (use 0 for no expiration)'),
                        type=int, default=1)
    parser.add_argument('-qto', '--quest-timezone-offset',
                        help=('Minutes between localtime and UTC of the area being scanned'),
                        type=int, default=0)
    parser.add_argument('-jit', '--jitter',
                        help=('Apply jitter to coordinates for teleport scheduling'),
                        action='store_true', default=True)
    parser.add_argument('-mn', '--mapname',
                        help=('Name for the map in the HTML'),
                        type=str, default='RocketMapPlusPlus')
    parser.add_argument('-df', '--devices-file',
                        help=('Device file with trusted devices'),
                        default='')
    group = parser.add_argument_group('Database')
    group.add_argument(
        '--db-name', help='Name of the database to be used.', required=True)
    group.add_argument(
        '--db-user', help='Username for the database.', required=True)
    group.add_argument(
        '--db-pass', help='Password for the database.', required=True)
    group.add_argument(
        '--db-host',
        help='IP or hostname for the database.',
        default='127.0.0.1')
    group.add_argument(
        '--db-port', help='Port for the database.', type=int, default=3306)
    group.add_argument(
        '--db-threads',
        help=('Number of db threads; increase if the db ' +
              'queue falls behind.'),
        type=int,
        default=1)
    group = parser.add_argument_group('Database Cleanup')
    group.add_argument('-DC', '--db-cleanup',
                       help='Enable regular database cleanup thread.',
                       action='store_true', default=False)
    group.add_argument('-DCw', '--db-cleanup-worker',
                       help=('Clear worker status from database after X ' +
                             'minutes of inactivity. ' +
                             'Default: 30, 0 to disable.'),
                       type=int, default=30)
    group.add_argument('-DCp', '--db-cleanup-pokemon',
                       help=('Clear pokemon from database X hours ' +
                             'after they disappeared. ' +
                             'Default: 0, 0 to disable.'),
                       type=int, default=0)
    group.add_argument('-DCg', '--db-cleanup-gym',
                       help=('Clear gym details from database X hours ' +
                             'after last gym scan. ' +
                             'Default: 8, 0 to disable.'),
                       type=int, default=8)
    group.add_argument('-DCs', '--db-cleanup-spawnpoint',
                       help=('Clear spawnpoint from database X hours ' +
                             'after last valid scan. ' +
                             'Default: 720, 0 to disable.'),
                       type=int, default=720)
    group.add_argument('-DCf', '--db-cleanup-forts',
                       help=('Clear gyms and pokestops from database X hours '
                             'after last valid scan. '
                             'Default: 0, 0 to disable.'),
                       type=int, default=0)
    parser.add_argument(
        '-wh',
        '--webhook',
        help='Define URL(s) to POST webhook information to.',
        default=None,
        dest='webhooks',
        action='append')
    parser.add_argument('-gi', '--gym-info',
                        help=('Get all details about gyms (causes an ' +
                              'additional API hit for every gym).'),
                        action='store_true', default=False)
    parser.add_argument(
        '--wh-types',
        help=('Defines the type of messages to send to webhooks.'),
        choices=[
            'pokemon', 'gym', 'raid', 'egg', 'tth', 'gym-info',
            'pokestop', 'lure', 'captcha', 'quest', 'pokemon-iv',
            'devices'
        ],
        action='append',
        default=[])
    parser.add_argument('--wh-threads',
                        help=('Number of webhook threads; increase if the ' +
                              'webhook queue falls behind.'),
                        type=int, default=1)
    parser.add_argument('-whc', '--wh-concurrency',
                        help=('Async requests pool size.'), type=int,
                        default=25)
    parser.add_argument('-whr', '--wh-retries',
                        help=('Number of times to retry sending webhook ' +
                              'data on failure.'),
                        type=int, default=3)
    parser.add_argument('-whct', '--wh-connect-timeout',
                        help=('Connect timeout (in seconds) for webhook' +
                              ' requests.'),
                        type=float, default=1.0)
    parser.add_argument('-whrt', '--wh-read-timeout',
                        help=('Read timeout (in seconds) for webhook' +
                              'requests.'),
                        type=float, default=1.0)
    parser.add_argument('-whbf', '--wh-backoff-factor',
                        help=('Factor (in seconds) by which the delay ' +
                              'until next retry will increase.'),
                        type=float, default=0.25)
    parser.add_argument('-whlfu', '--wh-lfu-size',
                        help='Webhook LFU cache max size.', type=int,
                        default=2500)
    parser.add_argument('-whfi', '--wh-frame-interval',
                        help=('Minimum time (in ms) to wait before sending the'
                              + ' next webhook data frame.'), type=int,
                        default=500)
    parser.add_argument('--ssl-certificate',
                        help='Path to SSL certificate file.')
    parser.add_argument('--ssl-privatekey',
                        help='Path to SSL private key file.')
    parser.add_argument('-ps', '--print-status',
                        help=('Show a status screen instead of log ' +
                              'messages. Can switch between status and ' +
                              'logs by pressing enter.  Optionally specify ' +
                              '"logs" to startup in logging mode.'),
                        nargs='?', const='status', default=False,
                        metavar='logs')
    parser.add_argument('-slt', '--stats-log-timer',
                        help='In log view, list per hr stats every X seconds',
                        type=int, default=0)
    parser.add_argument('-odt', '--on-demand_timeout',
                        help=('Pause searching while web UI is inactive ' +
                              'for this timeout (in seconds).'),
                        type=int, default=0)
    parser.add_argument('--disable-blacklist',
                        help=('Disable the global anti-scraper IP blacklist.'),
                        action='store_true', default=False)
    parser.add_argument('-tp', '--trusted-proxies', default=[],
                        action='append',
                        help=('Enables the use of X-FORWARDED-FOR headers ' +
                              'to identify the IP of clients connecting ' +
                              'through these trusted proxies.'))
    parser.add_argument('--no-file-logs',
                        help=('Disable logging to files. ' +
                              'Does not disable --access-logs.'),
                        action='store_true', default=False)
    parser.add_argument('--log-path',
                        help=('Defines directory to save log files to.'),
                        default='logs/')
    parser.add_argument('--log-filename',
                        help=('Defines the log filename to be saved.'
                              ' Allows date formatting, and replaces <SN>'
                              " with the instance's status name. Read the"
                              ' python time module docs for details.'
                              ' Default: %%Y%%m%%d_%%H%%M_<SN>.log.'),
                        default='%Y%m%d_%H%M_<SN>.log'),
    parser.add_argument('--dump',
                        help=('Dump censored debug info about the ' +
                              'environment and auto-upload to ' +
                              'hastebin.com.'),
                        action='store_true', default=False)
    parser.add_argument('-exg', '--ex-gyms',
                        help=('Fetch OSM parks within geofence and flag ' +
                              'gyms that are candidates for EX raids. ' +
                              'Only required once per area.'),
                        action='store_true', default=False)
    parser.add_argument('-gf', '--geofence-file',
                        help=('Geofence file to define outer borders of the ' +
                              'scan area.'),
                        default='')
    parser.add_argument('-gef', '--geofence-excluded-file',
                        help=('File to define excluded areas inside scan ' +
                              'area. Regarded this as inverted geofence. ' +
                              'Can be combined with geofence-file.'),
                        default='')
    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument('-v',
                         help=('Show debug messages from RocketMap ' +
                               'and pgoapi. Can be repeated up to 3 times.'),
                         action='count', default=0, dest='verbose')
    verbose.add_argument('--verbosity',
                         help=('Show debug messages from RocketMap ' +
                               'and pgoapi.'),
                         type=int, dest='verbose')
    rarity = parser.add_argument_group('Dynamic Rarity')
    rarity.add_argument('-Rh', '--rarity-hours',
                        help=('Number of hours of Pokemon data to use ' +
                              'to calculate dynamic rarity. Decimals ' +
                              'allowed. Default: 48, 0 to use all data.'),
                        type=float, default=48)
    rarity.add_argument('-Rf', '--rarity-update-frequency',
                        help=('How often (in minutes) the dynamic rarity ' +
                              'should be updated. Decimals allowed. ' +
                              'Default: 0, 0 to disable.'),
                        type=float, default=60)
    statusp = parser.add_argument_group('Status Page')
    statusp.add_argument('-SPp', '--status-page-password', default=None,
                         help='Set the status page password.')
    statusp.add_argument('-SPf', '--status-page-filter',
                         help=('Filter worker status that are inactive for ' +
                               'X minutes. Default: 30, 0 to disable.'),
                         type=int, default=30)
    parser.add_argument('-sn', '--status-name', default=str(os.getpid()),
                        help=('Enable status page database update using ' +
                              'STATUS_NAME as main worker name.'))
    group = parser.add_argument_group('Discord User Authentication')
    group.add_argument('-UA', '--user-auth',
                       help='Require end-users to authenticate using Discord.',
                       action='store_true', default=False)
    group.add_argument('-UAv', '--user-auth-validity',
                       help=('Check every X hours if user authentication ' +
                             'is still valid and refresh access token.'),
                       type=int, default=3600)
    group.add_argument('-UAbc', '--user-auth-block-concurrent',
                       help=('Block user access for X hours if concurrent ' +
                             'logins are detected. Default: 0 (disabled).'),
                       type=int, default=0)
    group.add_argument('-UAsk', '--user-auth-secret-key', default=None,
                       help='Secret key to encrypt session cookies. '
                            'Use a randomly generated string.')
    group.add_argument('-UAcid', '--user-auth-client-id', default=None,
                       help='Discord Client ID for user authentication.')
    group.add_argument('-UAcs', '--user-auth-client-secret', default=None,
                       help='Discord Client secret for user authentication.')
    group.add_argument('-UAbt', '--user-auth-bot-token', default=None,
                       help='Discord Bot Token required for fetching user '
                            'roles within the required guild.')
    group.add_argument('-UAgr', '--user-auth-guild-required', default=None,
                       help='Discord Guild the users must join to be able '
                            'to access the map.')
    group.add_argument('-UAgi', '--user-auth-guild-invite', default=None,
                       help='Invitation link for the required guild.')
    group.add_argument('-UArr', '--user-auth-role-required',
                       help='Discord Guild Role name(s) the users must have '
                            '(at least one) in order to access the map.',
                       default=[], action='append')
    group.add_argument('-UAri', '--user-auth-role-invite', default=None,
                       help='Invitation link for the required role.')
    parser.add_argument('-gen', '--generate-images',
                        help='Use ImageMagick to generate gym images on demand.',
                        action='store_true', default=False)
    parser.set_defaults(DEBUG=False)

    args = parser.parse_args()

    # Allow status name and date formatting in log filename.
    args.log_filename = strftime(args.log_filename)
    args.log_filename = args.log_filename.replace('<sn>', '<SN>')
    args.log_filename = args.log_filename.replace('<SN>', args.status_name)

    if args.user_auth:
        if not args.user_auth_secret_key:
            print(sys.argv[0] +
                  ": error: arguments -UAs/--user-auth-secret is required.")
            sys.exit(1)

        if not args.user_auth_bot_token:
            print(sys.argv[0] +
                  ": error: arguments -UAbt/--user-auth-bot-token is " +
                  "required for fetching user roles from Discord.")
            sys.exit(1)

        if args.user_auth_guild_required and not args.user_auth_guild_invite:
            print(sys.argv[0] +
                  ": error: arguments -UAgi/--user-auth-guild-invite is " +
                  "required when using -UAgr/--user-auth-guild-required.")
            sys.exit(1)

        if args.user_auth_role_required and not args.user_auth_guild_required:
            print(sys.argv[0] +
                  ": error: arguments -UAgr/--user-auth-guild-required is " +
                  "required when using -UArr/--user-auth-role-required.")
            sys.exit(1)

        if args.user_auth_role_required and not args.user_auth_role_invite:
            args.user_auth_role_invite = args.user_auth_guild_invite

    if args.location is None:
        parser.print_usage()
        print(sys.argv[0] +
              ": error: arguments -l/--location is required.")
        sys.exit(1)

    args.locales_dir = 'static/dist/locales'
    args.data_dir = 'static/dist/data'

    return args


def now():
    # The fact that you need this helper...
    return int(time.time())


# Gets the seconds past the hour.
def cur_sec():
    return (60 * time.gmtime().tm_min) + time.gmtime().tm_sec


# Gets the total seconds past the hour for a given date.
def date_secs(d):
    return d.minute * 60 + d.second


# Checks to see if test is between start and end accounting for hour
# wraparound.
def clock_between(start, test, end):
    return ((start <= test <= end and start < end) or
            (not (end <= test <= start) and start > end))


# Return the s2sphere cellid token from a location.
def cellid(loc):
    return int(
        CellId.from_lat_lng(LatLng.from_degrees(loc[0], loc[1])).to_token(),
        16)


# Return approximate distance in meters.
def distance(pos1, pos2):
    return haversine((tuple(pos1))[0:2], (tuple(pos2))[0:2])


# Return True if distance between two locs is less than distance in meters.
def in_radius(loc1, loc2, radius):
    return distance(loc1, loc2) < radius


def i8ln(word):
    if not hasattr(i8ln, 'dictionary'):
        args = get_args()
        file_path = os.path.join(
            args.root_path,
            args.locales_dir,
            '{}.min.json'.format(args.locale))
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                i8ln.dictionary = json.loads(f.read())
        else:
            # If locale file is not found we set an empty dict to avoid
            # checking the file every time, we skip the warning for English as
            # it is not expected to exist.
            if not args.locale == 'en':
                log.warning(
                    'Skipping translations - unable to find locale file: %s',
                    file_path)
            i8ln.dictionary = {}
    if word in i8ln.dictionary:
        return i8ln.dictionary[word]
    else:
        return word


# Thread function for periodical enc list updating.
def dynamic_loading_refresher(file_list):
    # We're on a 60-second timer.
    refresh_time_sec = 60

    while True:
        # Wait (x-1) seconds before refresh, min. 1s.
        time.sleep(max(1, refresh_time_sec - 1))

        for arg_type, filename in file_list.items():
            try:
                # IV/CP scanning.
                if filename:
                    # Only refresh if the file has changed.
                    current_time_sec = time.time()
                    file_modified_time_sec = os.path.getmtime(filename)
                    time_diff_sec = current_time_sec - file_modified_time_sec

                    # File has changed in the last refresh_time_sec seconds.
                    if time_diff_sec < refresh_time_sec:
                        args = get_args()
                        with open(filename) as f:
                            new_list = frozenset([int(l.strip()) for l in f])
                            setattr(args, arg_type, new_list)
                            log.info('New %s is: %s.', arg_type, new_list)
                    else:
                        log.debug('No change found in %s.', filename)
            except Exception as e:
                log.exception('Exception occurred while' +
                              ' updating %s: %s.', arg_type, e)


def get_pokemon_data(pokemon_id):
    if not hasattr(get_pokemon_data, 'pokemon'):
        args = get_args()
        file_path = os.path.join(
            args.root_path,
            args.data_dir,
            'pokemon.min.json')

        with open(file_path, 'r') as f:
            get_pokemon_data.pokemon = json.loads(f.read())
    return get_pokemon_data.pokemon[str(pokemon_id)]


def get_pokemon_name(pokemon_id):
    return i8ln(get_pokemon_data(pokemon_id)['name'])


def get_quest_icon(reward_type, reward_item):
    result = ""
    if reward_type == "POKEMON_ENCOUNTER" and reward_item is not None:
        result = str(_POKEMONID.values_by_name[reward_item].number)
    elif reward_type == "STARDUST":
        result = "STARDUST"
    elif reward_item is not None:
        result = reward_item
    return result

def get_quest_quest_text(quest_json):
    if quest_json is None:
       return ""

    quest_text = u""

    quest_type = quest_json.get('questType', "")
    quest_goal = quest_json.get('goal', {})
    quest_goal_conditions = quest_goal.get('condition', [])
    quest_goal_target = quest_goal.get('target', 0)

    if quest_type == "QUEST_UNKNOWN_TYPE":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_FIRST_CATCH_OF_THE_DAY":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_FIRST_POKESTOP_OF_THE_DAY":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_MULTI_PART":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_CATCH_POKEMON":
        pokemon_type_text = ""
        pokemon_category_text = ""
        weather_boost_text = ""

        quest_catch_pokemon = quest_json.get('catchPokemon', {})

        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            if quest_goal_condition_type == "WITH_POKEMON_TYPE":
                withPokemonType = quest_goal_condition.get('withPokemonType', {})
                pokemon_types = withPokemonType.get('pokemonType', [])
                i = 0
                for pokemon_type in pokemon_types:
                    i += 1
                    if len(pokemon_type_text) == 0:
                        pokemon_type_text = u" "
                    elif i == len(pokemon_types):
                        pokemon_type_text += " or "
                    else:
                        pokemon_type_text += ", "
                    pokemon_type_text += pokemon_type[13:].title()
                if len(pokemon_type_text) > 0:
                    pokemon_type_text += "-type"
            elif quest_goal_condition_type == "WITH_POKEMON_CATEGORY":
                withPokemonCategory = quest_goal_condition.get('withPokemonCategory', {})
                pokemon_ids = withPokemonCategory.get('pokemonIds', [])
                i = 0
                for pokemon_id in pokemon_ids:
                    i += 1
                    if len(pokemon_category_text) == 0:
                        pokemon_category_text = u" "
                    elif i == len(pokemon_ids):
                        pokemon_category_text += " or "
                    else:
                        pokemon_category_text += ", "
                    pokemon_category_text += pokemon_id.title()
            elif quest_goal_condition_type == "WITH_WEATHER_BOOST":
                weather_boost_text = " with Weather Boost"
            else:
                return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if len(pokemon_category_text) == 0:
            pokemon_category_text = u" Pok\u00E9mon"

        if quest_goal_target == 1:
            quest_text = u"Catch a{}{}{}".format(pokemon_type_text, pokemon_category_text, weather_boost_text)
        else:
            quest_text = u"Catch {}{}{}{}".format(quest_goal_target, pokemon_type_text, pokemon_category_text, weather_boost_text)
    elif quest_type == "QUEST_SPIN_POKESTOP":
        unique_pokestop_text = ""

        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            if quest_goal_condition_type == "WITH_UNIQUE_POKESTOP":
                unique_pokestop_text = " you haven't visited before"
            else:
                return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = u"Spin a Pok\u00E9Stop or Gym{}".format(unique_pokestop_text)
        else:
            quest_text = u"Spin {} Pok\u00E9Stops or Gyms{}".format(quest_goal_target, unique_pokestop_text)
    elif quest_type == "QUEST_HATCH_EGG":
        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = "Hatch an Egg"
        else:
            quest_text = "Hatch {} Eggs".format(quest_goal_target)
    elif quest_type == "QUEST_COMPLETE_GYM_BATTLE":
        NeedToWin = False
        SuperEffecitveCharge = False

        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            if quest_goal_condition_type == "WITH_WIN_GYM_BATTLE_STATUS":
                NeedToWin = True
            elif quest_goal_condition_type == "WITH_SUPER_EFFECTIVE_CHARGE":
                SuperEffecitveCharge = True
            else:
                return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            if SuperEffecitveCharge:
                quest_text = "Use a supereffective Charged Attack in a Gym battle"
            elif NeedToWin:
                quest_text = "Win a Gym battle"
            else:
                quest_text = "Battle in a Gym"
        else:
            if SuperEffecitveCharge:
                quest_text = "Use a supereffective Charged Attack in {} Gym battles".format(quest_goal_target)
            elif NeedToWin:
                quest_text = "Win {} Gym battles".format(quest_goal_target)
            else:
                quest_text = "Battle in a Gym {} times".format(quest_goal_target)

    elif quest_type == "QUEST_COMPLETE_RAID_BATTLE":
        NeedToWin = False
        raid_levels = []
        raid_level_text = ""

        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            if quest_goal_condition_type == "WITH_WIN_RAID_STATUS":
                NeedToWin = True
            elif quest_goal_condition_type == "WITH_RAID_LEVEL":
                quest_goal_condition_with_raid_level = quest_goal_condition.get('withRaidLevel', {})
                raid_levels = quest_goal_condition_with_raid_level.get('raidLevel', [])
            else:
                return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if len(raid_levels) == 0 or len(raid_levels) == 5:
            raid_level_text = ""
        elif len(raid_levels) == 1:
            raid_level_text = " level " + raid_levels[0][11:]
        else:
            raid_level_text = " level " + raid_levels[0][11:] + " or higher"

        if quest_goal_target == 1:
            if NeedToWin:
                quest_text = "Win a{} Raid".format(raid_level_text)
            else:
                quest_text = "Battle in a{} Raid".format(raid_level_text)
        else:
            if NeedToWin:
                quest_text = "Win {}{} Raids".format(quest_goal_target, raid_level_text)
            else:
                quest_text = "Battle in {}{} Raids".format(quest_goal_target, raid_level_text)
    elif quest_type == "QUEST_COMPLETE_QUEST":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_TRANSFER_POKEMON":
        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = u"Transfer a Pok\u00E9mon"
        else:
            quest_text = u"Transfer {} Pok\u00E9mon".format(quest_goal_target)
    elif quest_type == "QUEST_FAVORITE_POKEMON":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_AUTOCOMPLETE":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_USE_BERRY_IN_ENCOUNTER":
        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = u"Use a Berry to help catch Pok\u00E9mon"
        else:
            quest_text = u"Use {} Berries to help catch Pok\u00E9mon".format(quest_goal_target)
    elif quest_type == "QUEST_UPGRADE_POKEMON":
        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = u"Power up a Pok\u00E9mon"
        else:
            quest_text = u"Power up Pok\u00E9mon {} times".format(quest_goal_target)
    elif quest_type == "QUEST_EVOLVE_POKEMON":
        pokemon_type_text = ""
        pokemon_category_text = ""

        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            if quest_goal_condition_type == "WITH_POKEMON_TYPE":
                withPokemonType = quest_goal_condition.get('withPokemonType', {})
                pokemon_types = withPokemonType.get('pokemonType', [])
                i = 0
                for pokemon_type in pokemon_types:
                    i += 1
                    if len(pokemon_type_text) == 0:
                        pokemon_type_text = " "
                    elif i == len(pokemon_types):
                        pokemon_type_text += " or "
                    else:
                        pokemon_type_text += ", "
                    pokemon_type_text += pokemon_type[13:].title()
                if len(pokemon_type_text) > 0:
                    pokemon_type_text += "-type"
            elif quest_goal_condition_type == "WITH_POKEMON_CATEGORY":
                withPokemonCategory = quest_goal_condition.get('withPokemonCategory', {})
                pokemon_ids = withPokemonCategory.get('pokemonIds', [])
                i = 0
                for pokemon_id in pokemon_ids:
                    i += 1
                    if len(pokemon_category_text) == 0:
                        pokemon_category_text = " "
                    elif i == len(pokemon_ids):
                        pokemon_category_text += " or "
                    else:
                        pokemon_category_text += ", "
                    pokemon_category_text += pokemon_id.title()
            else:
                return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if len(pokemon_category_text) == 0:
            pokemon_category_text = u" Pok\u00E9mon"

        if quest_goal_target == 1:
            quest_text = u"Evolve a{}{}".format(pokemon_type_text, pokemon_category_text)
        else:
            quest_text = u"Evolve {}{}{}".format(quest_goal_target, pokemon_type_text, pokemon_category_text)
    elif quest_type == "QUEST_LAND_THROW":
        NiceThrow = False
        GreatThrow = False
        ExcellentThrow = False
        CurveBall = False
        InARow = False
        n_text = ""
        throw_type_text = ""
        curveball_text = ""
        in_a_row_text = ""

        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            if quest_goal_condition_type == "WITH_THROW_TYPE":
                withThrowType = quest_goal_condition.get('withThrowType', {})
                ThrowType = withThrowType.get('throwType', "")
                if ThrowType == "ACTIVITY_CATCH_NICE_THROW":
                    NiceThrow = True
                elif ThrowType == "ACTIVITY_CATCH_GREAT_THROW":
                    GreatThrow = True
                elif ThrowType == "ACTIVITY_CATCH_EXCELLENT_THROW":
                    ExcellentThrow = True
            elif quest_goal_condition_type == "WITH_THROW_TYPE_IN_A_ROW":
                InARow =  True
                withThrowType = quest_goal_condition.get('withThrowType', {})
                ThrowType = withThrowType.get('throwType', "")
                if ThrowType == "ACTIVITY_CATCH_NICE_THROW":
                    NiceThrow = True
                elif ThrowType == "ACTIVITY_CATCH_GREAT_THROW":
                    GreatThrow = True
                elif ThrowType == "ACTIVITY_CATCH_EXCELLENT_THROW":
                    ExcellentThrow = True
            elif quest_goal_condition_type == "WITH_CURVE_BALL":
                CurveBall = True
            else:
                return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if NiceThrow:
            throw_type_text = " Nice"
        elif GreatThrow:
            throw_type_text = " Great"
        elif ExcellentThrow:
            n_text = "n"
            throw_type_text = " Excellent"
        if CurveBall:
            curveball_text = " Curveball"
        if InARow:
            in_a_row_text = " in a row"

        if quest_goal_target == 1:
           quest_text = "Make a{}{}{} Throw".format(n_text, throw_type_text, curveball_text)
        else:
           quest_text = "Make {}{}{} Throws{}".format(quest_goal_target, throw_type_text, curveball_text, in_a_row_text)

    elif quest_type == "QUEST_GET_BUDDY_CANDY":
        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = "Earn a Candy walking with your buddy"
        else:
            quest_text = "Earn {} Candies walking with your buddy".format(quest_goal_target)
    elif quest_type == "QUEST_BADGE_RANK":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_PLAYER_LEVEL":
        quest_text = "Reach level {}".format(quest_goal_target)
    elif quest_type == "QUEST_JOIN_RAID":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_COMPLETE_BATTLE":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_ADD_FRIEND":
        return "Quest Not Supported! - {}".format(quest_type)
    elif quest_type == "QUEST_TRADE_POKEMON":
        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = u"Trade a Pok\u00E9mon"
        else:
            quest_text = u"Trade {} Pok\u00E9mon".format(quest_goal_target)
    elif quest_type == "QUEST_SEND_GIFT":
        for quest_goal_condition in quest_goal_conditions:
            quest_goal_condition_type = quest_goal_condition.get('type', "")
            return "Condition Not Supported! - {} -> {}".format(quest_type, quest_goal_condition_type)

        if quest_goal_target == 1:
            quest_text = "Send a Gift to a friend"
        else:
            quest_text = "Send {} Gifts to friends".format(quest_goal_target)
    elif quest_type == "QUEST_EVOLVE_INTO_POKEMON":
        return "Quest Not Supported! - {}".format(quest_type)
    else:
        return "Quest Not Supported! - {}".format(quest_type)

    if quest_text == "":
        quest_text = "Not Supported"

    return quest_text

def get_quest_reward_text(quest_json):
    if quest_json is None:
       return ""

    reward_text = u""

    quest_rewards = quest_json.get('questRewards', [])

    for quest_reward in quest_rewards:
        reward_type = quest_reward.get('type', "")

        if reward_type == "UNSET":
            return "Reward Not Supported! - {}".format(reward_type)
        elif reward_type == "EXPERIENCE":
            return "Reward Not Supported! - {}".format(reward_type)
        elif reward_type == "ITEM":
            reward_item = quest_reward.get('item', {})
            reward_item_item = reward_item.get('item', "")
            reward_item_amount = reward_item.get('amount', 0)

            if reward_item_item == "ITEM_POKE_BALL":
                reward_text = u"{} Pok\u00E9 {}".format(reward_item_amount, "Ball" if reward_item_amount == 1 else "Balls")
            elif reward_item_item == "ITEM_GREAT_BALL":
                reward_text = "{} Great {}".format(reward_item_amount, "Ball" if reward_item_amount == 1 else "Balls")
            elif reward_item_item == "ITEM_ULTRA_BALL":
                reward_text = "{} Ultra {}".format(reward_item_amount, "Ball" if reward_item_amount == 1 else "Balls")
            elif reward_item_item == "ITEM_MASTER_BALL":
                reward_text = "{} Master {}".format(reward_item_amount, "Ball" if reward_item_amount == 1 else "Balls")
            elif reward_item_item == "ITEM_PREMIER_BALL":
                reward_text = "{} Premier {}".format(reward_item_amount, "Ball" if reward_item_amount == 1 else "Balls")
            elif reward_item_item == "ITEM_POTION":
                reward_text = "{} {}".format(reward_item_amount, "Potion" if reward_item_amount == 1 else "Potions")
            elif reward_item_item == "ITEM_SUPER_POTION":
                reward_text = "{} Super {}".format(reward_item_amount, "Potion" if reward_item_amount == 1 else "Potions")
            elif reward_item_item == "ITEM_HYPER_POTION":
                reward_text = "{} Hyper {}".format(reward_item_amount, "Potion" if reward_item_amount == 1 else "Potions")
            elif reward_item_item == "ITEM_MAX_POTION":
                reward_text = "{} Max {}".format(reward_item_amount, "Potion" if reward_item_amount == 1 else "Potions")
            elif reward_item_item == "ITEM_REVIVE":
                reward_text = "{} {}".format(reward_item_amount, "Revive" if reward_item_amount == 1 else "Revives")
            elif reward_item_item == "ITEM_MAX_REVIVE":
                reward_text = "{} Max {}".format(reward_item_amount, "Revive" if reward_item_amount == 1 else "Revives")
            elif reward_item_item == "ITEM_RAZZ_BERRY":
                reward_text = "{} Razz {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_BLUK_BERRY":
                reward_text = "{} Bluk {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_NANAB_BERRY":
                reward_text = "{} Nanab {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_WEPAR_BERRY":
                reward_text = "{} Wepar {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_PINAP_BERRY":
                reward_text = "{} Pinap {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_GOLDEN_RAZZ_BERRY":
                reward_text = "{} Golden Razz {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_GOLDEN_NANAB_BERRY":
                reward_text = "{} Golden Nanab {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_GOLDEN_PINAP_BERRY":
                reward_text = "{} Silver Pinap {}".format(reward_item_amount, "Berry" if reward_item_amount == 1 else "Berries")
            elif reward_item_item == "ITEM_RARE_CANDY":
                reward_text = "{} Rare {}".format(reward_item_amount, "Candy" if reward_item_amount == 1 else "Candies")
            else:
                return "Reward Item Not Supported! - {} -> {} ({})".format(reward_type, reward_item_item, reward_item_amount)

        elif reward_type == "STARDUST":
            reward_amount = quest_reward.get('stardust', 0)
            reward_text = "{} Stardust".format(reward_amount)
        elif reward_type == "CANDY":
            return "Reward Not Supported! - {}".format(reward_type)
        elif reward_type == "AVATAR_CLOTHING":
            return "Reward Not Supported! - {}".format(reward_type)
        elif reward_type == "QUEST":
            return "Reward Not Supported! - {}".format(reward_type)
        elif reward_type == "POKEMON_ENCOUNTER":
            reward_pokemon_encounter = quest_reward.get('pokemonEncounter', {})
            reward_pokemon_encounter_pokemonid = reward_pokemon_encounter.get('pokemonId', "")
            reward_text = "{} Encounter".format(reward_pokemon_encounter_pokemonid.title())
        else:
            return "Reward Not Supported! - {}".format(reward_type)

    if reward_text == "":
        reward_text = "Not Supported"

    return reward_text

def get_pokemon_types(pokemon_id):
    pokemon_types = get_pokemon_data(pokemon_id)['types']
    return map(lambda x: {"type": i8ln(x['type']), "color": x['color']},
               pokemon_types)


def get_moves_data(move_id):
    if not hasattr(get_moves_data, 'moves'):
        args = get_args()
        file_path = os.path.join(
            args.root_path,
            args.data_dir,
            'moves.min.json')

        with open(file_path, 'r') as f:
            get_moves_data.moves = json.loads(f.read())
    return get_moves_data.moves[str(move_id)]


def get_move_name(move_id):
    return i8ln(get_moves_data(move_id)['name'])


def get_move_damage(move_id):
    return i8ln(get_moves_data(move_id)['damage'])


def get_move_energy(move_id):
    return i8ln(get_moves_data(move_id)['energy'])


def get_move_type(move_id):
    move_type = get_moves_data(move_id)['type']
    return {'type': i8ln(move_type), 'type_en': move_type}


def dottedQuadToNum(ip):
    return struct.unpack("!L", socket.inet_aton(ip))[0]


# Generate random device info.
# Original by Noctem.
IPHONES = {'iPhone6,1': 'N51AP',
           'iPhone6,2': 'N53AP',
           'iPhone7,1': 'N56AP',
           'iPhone7,2': 'N61AP',
           'iPhone8,1': 'N71AP',
           'iPhone8,2': 'N66AP',
           'iPhone8,4': 'N69AP',
           'iPhone9,1': 'D10AP',
           'iPhone9,2': 'D11AP',
           'iPhone9,3': 'D101AP',
           'iPhone9,4': 'D111AP',
           'iPhone10,1': 'D20AP',
           'iPhone10,2': 'D21AP',
           'iPhone10,3': 'D22AP',
           'iPhone10,4': 'D201AP',
           'iPhone10,5': 'D211AP',
           'iPhone10,6': 'D221AP'}


def generate_device_info(identifier):
    md5 = hashlib.md5()
    md5.update(identifier)
    pick_hash = int(md5.hexdigest(), 16)

    device_info = {'device_brand': 'Apple', 'device_model': 'iPhone',
                   'hardware_manufacturer': 'Apple',
                   'firmware_brand': 'iPhone OS'}
    devices = tuple(IPHONES.keys())

    ios9 = ('9.0', '9.0.1', '9.0.2', '9.1', '9.2', '9.2.1', '9.3', '9.3.1',
            '9.3.2', '9.3.3', '9.3.4', '9.3.5')
    # 10.0 was only for iPhone 7 and 7 Plus, and is rare.
    ios10 = ('10.0.1', '10.0.2', '10.0.3', '10.1', '10.1.1', '10.2', '10.2.1',
             '10.3', '10.3.1', '10.3.2', '10.3.3')
    ios11 = ('11.0.1', '11.0.2', '11.0.3', '11.1', '11.1.1', '11.1.2')

    device_pick = devices[pick_hash % len(devices)]
    device_info['device_model_boot'] = device_pick
    device_info['hardware_model'] = IPHONES[device_pick]
    device_info['device_id'] = md5.hexdigest()

    if device_pick in ('iPhone10,1', 'iPhone10,2', 'iPhone10,3',
                       'iPhone10,4', 'iPhone10,5', 'iPhone10,6'):
        # iPhone 8/8+ and X started on 11.
        ios_pool = ios11
    elif device_pick in ('iPhone9,1', 'iPhone9,2', 'iPhone9,3', 'iPhone9,4'):
        # iPhone 7/7+ started on 10.
        ios_pool = ios10 + ios11
    elif device_pick == 'iPhone8,4':
        # iPhone SE started on 9.3.
        ios_pool = ('9.3', '9.3.1', '9.3.2', '9.3.3', '9.3.4', '9.3.5') \
                   + ios10 + ios11
    else:
        ios_pool = ios9 + ios10 + ios11

    device_info['firmware_type'] = ios_pool[pick_hash % len(ios_pool)]
    return device_info


def calc_pokemon_level(cp_multiplier):
    if cp_multiplier < 0.734:
        pokemon_level = (58.35178527 * cp_multiplier * cp_multiplier -
                         2.838007664 * cp_multiplier + 0.8539209906)
    else:
        pokemon_level = 171.0112688 * cp_multiplier - 95.20425243
    pokemon_level = int((round(pokemon_level) * 2) / 2)
    return pokemon_level


@memoize
def gmaps_reverse_geolocate(gmaps_key, locale, location):
    # Find the reverse geolocation
    geolocator = GoogleV3(api_key=gmaps_key)

    player_locale = {
        'country': 'US',
        'language': locale,
        'timezone': 'America/Denver'
    }

    try:
        reverse = geolocator.reverse(location)
        address = reverse[-1].raw['address_components']
        country_code = 'US'

        # Find country component.
        for component in address:
            # Look for country.
            component_is_country = any([t == 'country'
                                        for t in component.get('types', [])])

            if component_is_country:
                country_code = component['short_name']
                break

        try:
            timezone = geolocator.timezone(location)
            player_locale.update({
                'country': country_code,
                'timezone': str(timezone)
            })
        except Exception as e:
            log.exception('Exception on Google Timezone API. '
                          + 'Please check that you have Google Timezone API'
                          + ' enabled for your API key'
                          + ' (https://developers.google.com/maps/'
                          + 'documentation/timezone/intro): %s.', e)
    except Exception as e:
        log.exception('Exception while obtaining player locale: %s.'
                      + ' Using default locale.', e)

    return player_locale


# Get a future_requests FuturesSession that supports asynchronous workers
# and retrying requests on failure.
# Setting up a persistent session that is re-used by multiple requests can
# speed up requests to the same host, as it'll re-use the underlying TCP
# connection.
def get_async_requests_session(num_retries, backoff_factor, pool_size,
                               status_forcelist=None):
    # Use requests & urllib3 to auto-retry.
    # If the backoff_factor is 0.1, then sleep() will sleep for [0.1s, 0.2s,
    # 0.4s, ...] between retries. It will also force a retry if the status
    # code returned is in status_forcelist.
    if status_forcelist is None:
        status_forcelist = [500, 502, 503, 504]
    session = FuturesSession(max_workers=pool_size)

    # If any regular response is generated, no retry is done. Without using
    # the status_forcelist, even a response with status 500 will not be
    # retried.
    retries = Retry(total=num_retries, backoff_factor=backoff_factor,
                    status_forcelist=status_forcelist)

    # Mount handler on both HTTP & HTTPS.
    session.mount('http://', HTTPAdapter(max_retries=retries,
                                         pool_connections=pool_size,
                                         pool_maxsize=pool_size))
    session.mount('https://', HTTPAdapter(max_retries=retries,
                                          pool_connections=pool_size,
                                          pool_maxsize=pool_size))

    return session


# Get common usage stats.
def resource_usage():
    platform = sys.platform
    proc = psutil.Process()

    with proc.oneshot():
        cpu_usage = psutil.cpu_times_percent()
        mem_usage = psutil.virtual_memory()
        net_usage = psutil.net_io_counters()

        usage = {
            'platform': platform,
            'PID': proc.pid,
            'MEM': {
                'total': mem_usage.total,
                'available': mem_usage.available,
                'used': mem_usage.used,
                'free': mem_usage.free,
                'percent_used': mem_usage.percent,
                'process_percent_used': proc.memory_percent()
            },
            'CPU': {
                'user': cpu_usage.user,
                'system': cpu_usage.system,
                'idle': cpu_usage.idle,
                'process_percent_used': proc.cpu_percent(interval=1)
            },
            'NET': {
                'bytes_sent': net_usage.bytes_sent,
                'bytes_recv': net_usage.bytes_recv,
                'packets_sent': net_usage.packets_sent,
                'packets_recv': net_usage.packets_recv,
                'errin': net_usage.errin,
                'errout': net_usage.errout,
                'dropin': net_usage.dropin,
                'dropout': net_usage.dropout
            },
            'connections': {
                'ipv4': len(proc.connections('inet4')),
                'ipv6': len(proc.connections('inet6'))
            },
            'thread_count': proc.num_threads(),
            'process_count': len(psutil.pids())
        }

        # Linux only.
        if platform == 'linux' or platform == 'linux2':
            usage['sensors'] = {
                'temperatures': psutil.sensors_temperatures(),
                'fans': psutil.sensors_fans()
            }
            usage['connections']['unix'] = len(proc.connections('unix'))
            usage['num_handles'] = proc.num_fds()
        elif platform == 'win32':
            usage['num_handles'] = proc.num_handles()

    return usage


# Log resource usage to any logger.
def log_resource_usage(log_method):
    usage = resource_usage()
    log_method('Resource usage: %s.', usage)


# Generic method to support periodic background tasks. Thread sleep could be
# replaced by a tiny sleep, and time measuring, but we're using sleep() for
# now to keep resource overhead to an absolute minimum.
def periodic_loop(f, loop_delay_ms):
    while True:
        # Do the thing.
        f()
        # zZz :bed:
        time.sleep(loop_delay_ms / 1000)


# Periodically log resource usage every 'loop_delay_ms' ms.
def log_resource_usage_loop(loop_delay_ms=60000):
    # Helper method to log to specific log level.
    def log_resource_usage_to_debug():
        log_resource_usage(log.debug)

    periodic_loop(log_resource_usage_to_debug, loop_delay_ms)


# Return shell call output as string, replacing any errors with the
# error's string representation.
def check_output_catch(command):
    try:
        result = subprocess.check_output(command,
                                         stderr=subprocess.STDOUT,
                                         shell=True)
    except Exception as ex:
        result = 'ERROR: ' + ex.output.replace(os.linesep, ' ')
    finally:
        return result.strip()


# Automatically censor all necessary fields. Lists will return their
# length, all other items will return 'empty_tag' if they're empty
# or 'censored_tag' if not.
def _censor_args_namespace(args, censored_tag, empty_tag):
    fields_to_censor = [
        'accounts',
        'accounts_L30',
        'username',
        'password',
        'auth_service',
        'proxy',
        'webhooks',
        'webhook_blacklist',
        'webhook_whitelist',
        'config',
        'accountcsv',
        'high_lvl_accounts',
        'geofence_file',
        'geofence_excluded_file',
        'ignorelist_file',
        'enc_whitelist_file',
        'webhook_whitelist_file',
        'webhook_blacklist_file',
        'db',
        'proxy_file',
        'log_path',
        'log_filename',
        'encrypt_lib',
        'ssl_certificate',
        'ssl_privatekey',
        'location',
        'captcha_key',
        'captcha_dsk',
        'external_hostname',
        'host',
        'port',
        'gmaps_key',
        'db_name',
        'db_user',
        'db_pass',
        'db_host',
        'db_port',
        'status_name',
        'status_page_password',
        'hash_key',
        'trusted_proxies',
        'data_dir',
        'locales_dir',
        'shared_config',
        'user_auth_secret_key',
        'user_auth_client_id',
        'user_auth_client_secret',
        'user_auth_bot_token',
        'user_auth_guild_required',
        'user_auth_guild_invite',
        'user_auth_role_required',
        'user_auth_role_invite'
    ]

    for field in fields_to_censor:
        # Do we have the field?
        if field in args:
            value = args[field]

            # Replace with length of list or censored tag.
            if isinstance(value, list):
                args[field] = len(value)
            else:
                if args[field]:
                    args[field] = censored_tag
                else:
                    args[field] = empty_tag

    return args


# Get censored debug info about the environment we're running in.
def get_censored_debug_info():
    CENSORED_TAG = '<censored>'
    EMPTY_TAG = '<empty>'
    args = _censor_args_namespace(vars(get_args()), CENSORED_TAG, EMPTY_TAG)

    # Get git status.
    status = check_output_catch('git status')
    log = check_output_catch('git log -1')
    remotes = check_output_catch('git remote -v')

    # Python, pip, node, npm.
    python = sys.version.replace(os.linesep, ' ').strip()
    pip = check_output_catch('pip -V')
    node = check_output_catch('node -v')
    npm = check_output_catch('npm -v')

    return {
        'args': args,
        'git': {
            'status': status,
            'log': log,
            'remotes': remotes
        },
        'versions': {
            'python': python,
            'pip': pip,
            'node': node,
            'npm': npm
        }
    }


# Post a string of text to a hasteb.in and retrieve the URL.
def upload_to_hastebin(text):
    log.info('Uploading info to hastebin.com...')
    response = requests.post('https://hastebin.com/documents', data=text)
    return response.json()['key']


# Get censored debug info & auto-upload to hasteb.in.
def get_debug_dump_link():
    debug = get_censored_debug_info()
    args = debug['args']
    git = debug['git']
    versions = debug['versions']

    # Format debug info for text upload.
    result = '''#######################
### RocketMap debug ###
#######################

## Versions:
'''

    # Versions first, for readability.
    result += '- Python: ' + versions['python'] + '\n'
    result += '- pip: ' + versions['pip'] + '\n'
    result += '- Node.js: ' + versions['node'] + '\n'
    result += '- npm: ' + versions['npm'] + '\n'

    # Next up is git.
    result += '\n\n' + '## Git:' + '\n'
    result += git['status'] + '\n'
    result += '\n\n' + git['remotes'] + '\n'
    result += '\n\n' + git['log'] + '\n'

    # And finally, our censored args.
    result += '\n\n' + '## Settings:' + '\n'
    result += pformat(args, width=1)

    # Upload to hasteb.in.
    return upload_to_hastebin(result)


def get_pokemon_rarity(total_spawns_all, total_spawns_pokemon):
    spawn_group = 'Common'

    spawn_rate_pct = total_spawns_pokemon / float(total_spawns_all)
    spawn_rate_pct = round(100 * spawn_rate_pct, 4)

    if spawn_rate_pct < 0.01:
        spawn_group = 'Ultra Rare'
    elif spawn_rate_pct < 0.03:
        spawn_group = 'Very Rare'
    elif spawn_rate_pct < 0.5:
        spawn_group = 'Rare'
    elif spawn_rate_pct < 1:
        spawn_group = 'Uncommon'

    return spawn_group


def device_worker_refresher(db_update_queue, wh_update_queue, args):
    from pogom.models import DeviceWorker

    refresh_time_sec = 60

    workers = {}
    deviceworkers = DeviceWorker.get_all()
    for worker in deviceworkers:
        workers[worker['deviceid']] = worker.copy()

    while True:
        deviceworkers = DeviceWorker.get_all()
        updateworkers = {}

        for worker in deviceworkers:
            needtosend = False
            if worker['deviceid'] not in workers:
                needtosend = True
                log.info("New device found: " + worker['deviceid'])
            else:
                last_updated = worker['last_updated']
                difference = (datetime.utcnow() - last_updated).total_seconds()
                if difference > 300 and worker['fetch'] != 'IDLE':
                    worker['fetch'] = 'IDLE'
                    updateworkers[worker['deviceid']] = worker
                    needtosend = True
                    log.info("Device stopped fetching: " + worker['deviceid'])
                last_scanned = worker['last_scanned']
                if last_scanned is None and worker['scanning'] != -1:
                    worker['scanning'] = -1
                    updateworkers[worker['deviceid']] = worker
                    needtosend = True
                    log.info("Device has never scanned " + worker['deviceid'])
                else:
                    difference = (datetime.utcnow() - last_scanned).total_seconds()
                    if difference < 60 and worker['scanning'] == 0:
                        worker['scanning'] = 1
                        updateworkers[worker['deviceid']] = worker
                        needtosend = True
                        log.info("Device is scanning " + worker['deviceid'])
                    elif difference > 60 and worker['scanning'] == 1:
                        worker['scanning'] = 0
                        updateworkers[worker['deviceid']] = worker
                        needtosend = True
                        log.info("Device went idle " + worker['deviceid'])
                    if worker['fetch'] != workers[worker['deviceid']]['fetch']:
                        needtosend = True
                        log.info("Device changed fetching endpoint: " + worker['deviceid'])
                    if worker['scanning'] != workers[worker['deviceid']]['scanning']:
                        needtosend = True
                        log.info("Device changed scanning status: " + worker['deviceid'])
            workers[worker['deviceid']] = worker.copy()

            if needtosend and 'devices' in args.wh_types:
                wh_worker = {
                    'uuid': worker['deviceid'],
                    'name': worker['name'],
                    'fetch': worker['fetch'],
                    'scanning': worker['scanning']
                }
                wh_update_queue.put(('devices', wh_worker))

        if updateworkers:
            db_update_queue.put((DeviceWorker, updateworkers))

        time.sleep(refresh_time_sec)


def dynamic_rarity_refresher():
    # If we import at the top, pogom.models will import pogom.utils,
    # causing the cyclic import to make some things unavailable.
    from pogom.models import Pokemon

    # Refresh every x hours.
    args = get_args()
    hours = args.rarity_hours
    root_path = args.root_path

    rarities_path = os.path.join(root_path, 'static/dist/data/rarity.json')
    update_frequency_mins = args.rarity_update_frequency
    refresh_time_sec = update_frequency_mins * 60

    while True:
        log.info('Updating dynamic rarity...')

        start = default_timer()
        db_rarities = Pokemon.get_spawn_counts(hours)
        total = db_rarities['total']
        pokemon = db_rarities['pokemon']

        # Store as an easy lookup table for front-end.
        rarities = {}

        for poke in pokemon:
            rarities[poke['pokemon_id']] = get_pokemon_rarity(total,
                                                              poke['count'])

        # Save to file.
        with open(rarities_path, 'w') as outfile:
            json.dump(rarities, outfile)

        duration = default_timer() - start
        log.info('Updated dynamic rarity. It took %.2fs for %d entries.',
                 duration,
                 total)

        # Wait x seconds before next refresh.
        log.debug('Waiting %d minutes before next dynamic rarity update.',
                  refresh_time_sec / 60)
        time.sleep(refresh_time_sec)


# Translate peewee model class attribute to database column name.
def peewee_attr_to_col(cls, field):
    field_column = getattr(cls, field)

    # Only try to do it on populated fields.
    if field_column is not None:
        field_column = field_column.db_column
    else:
        field_column = field

    return field_column
