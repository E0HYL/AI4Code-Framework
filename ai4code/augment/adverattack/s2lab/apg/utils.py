# -*- coding: utf-8 -*-

"""
utils.py
~~~~~~~~

A set of helper functions for use throughout the pipeline.

"""
import logging
import pickle
import subprocess
import sys
from timeit import default_timer as timer

import os
import ujson as json
from copy import deepcopy
from termcolor import colored

from apg.settings import config

red = lambda x: colored(x, 'red')
green = lambda x: colored(x, 'green')
yellow = lambda x: colored(x, 'yellow')
blue = lambda x: colored(x, 'blue')
magenta = lambda x: colored(x, 'magenta')
cyan = lambda x: colored(x, 'cyan')


def run_java_component(jar, args, timeout=None):
    """Wrapper for calling Java processes used for extraction and injection."""
    cmd = ['java', '-jar', jar, *args]
    logging.info(blue('Running command') + f': {" ".join(cmd)}')

    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.PIPE, timeout=timeout)
        return str(out, 'utf-8')
    except subprocess.TimeoutExpired:
        logging.warning(f'Java component {jar} timed out.')
    except subprocess.CalledProcessError as e:
        exception = "\nexit code :{0} \nSTDOUT :{1} \nSTDERROR : {2} ".format(
            e.returncode,
            e.output.decode(sys.getfilesystemencoding()),
            e.stderr.decode(sys.getfilesystemencoding()))
        logging.warning(
            f'SUBPROCESS Extraction EXCEPTION: {exception}')
    return ''


def flatten_list(nested_list):
    nested_list = deepcopy(nested_list)

    while nested_list:
        sublist = nested_list.pop(0)
        if isinstance(sublist, list):
            nested_list = sublist + nested_list
        else:
            yield sublist


def resolve_sample_filename(name, radix=0, ext='apk'):
    name = os.path.splitext(name)[0]  # remove 'ext' if present
    return ('{}/' + '{}/' * radix + '{}.{}').format(
        config['goodware_location'], *name[:radix], name, ext)


def sanitize_url_feature_name(feature):
    return feature.replace(".", "_").replace("/", "£").replace(":", "^")


def get_app_name(path):
    return os.path.basename(path).split('.')[0]


def seconds_to_time(seconds):
    """Return a nicely formatted elapsed time given the number of seconds."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return "%d days, %02d hours, %02d minutes, %02d seconds" % (d, h, m, s)


def configure_logging(run_tag, debug=True):
    fmt = f'[ {run_tag} | %(asctime)s | %(name)s | %(processName)s | %(levelname)s ] %(message)s'
    datefmt = '%Y-%m-%d | %H:%M:%S'
    level = logging.DEBUG if debug else 100  # 100 == no logging
    logging.basicConfig(level=level, format=fmt, datefmt=datefmt)


def log_failure(malware, msg, output_dir):
    malware = get_app_name(malware) if isinstance(
        malware, str) else get_app_name(malware.name)
    output = os.path.join(output_dir, 'failure', malware + '.txt')
    logging.error(red(msg))
    logging.error(f'Writing log to {output}')
    with open(output, 'wt') as f:
        f.write(f'{malware} @ {msg}\n')


def dump_pickle(data, output_dir, filename, overwrite=True):
    dump_data('pickle', data, output_dir, filename, overwrite)


def dump_json(data, output_dir, filename, overwrite=True):
    dump_data('json', data, output_dir, filename, overwrite)


def dump_data(protocol, data, output_dir, filename, overwrite=True):
    file_mode = 'w' if protocol == 'json' else 'wb'
    fname = os.path.join(output_dir, filename)
    logging.info(f'Dumping data to {fname}...')
    if overwrite or not os.path.exists(fname):
        with open(fname, file_mode) as f:
            if protocol == 'json':
                json.dump(data, f, indent=4)
            else:
                pickle.dump(data, f)


def stamp_start_time(output_dir):
    start_time = timer()
    logging.info(f'Logging start time @ {start_time}')
    dump_pickle(start_time, output_dir, 'start_time.p', overwrite=False)
    return start_time


# Set of 'dangerous permissions' as defined by Android (may be considered particularly suspicious):
# https://developer.android.com/guide/topics/permissions/overview#dangerous_permissions
dangerous_permissions = [
    'READ_CALENDAR',
    'WRITE_CALENDAR',
    'READ_CALL_LOG',
    'WRITE_CALL_LOG',
    'PROCESS_OUTGOING_CALLS',
    'CAMERA',
    'READ_CONTACTS',
    'WRITE_CONTACTS',
    'GET_ACCOUNTS',
    'ACCESS_FINE_LOCATION',
    'ACCESS_COARSE_LOCATION',
    'RECORD_AUDIO',
    'READ_PHONE_STATE',
    'READ_PHONE_NUMBERS',
    'CALL_PHONE',
    'ANSWER_PHONE_CALLS',
    'ADD_VOICEMAIL',
    'USE_SIP',
    'BODY_SENSORS',
    'SEND_SMS',
    'RECEIVE_SMS',
    'READ_SMS',
    'RECEIVE_WAP_PUSH',
    'RECEIVE_MMS',
    'READ_EXTERNAL_STORAGE',
    'WRITE_EXTERNAL_STORAGE']
