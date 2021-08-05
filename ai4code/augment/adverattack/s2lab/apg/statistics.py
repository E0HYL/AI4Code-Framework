# -*- coding: utf-8 -*-

"""
statistics.py
~~~~~~~~~~~~~

Helper classes for running the Java components that calculate cyclomatic complexity
for a given app or the number of classes present (both performed via Soot/FlowDroid).

"""
import os

import apg.utils as utils
from apg.settings import config


def get_avg_cc(malware):
    out = utils.run_java_component(
        config['cc_calculator'],
        [malware, config['android_sdk']], config['cc_calculator_timeout'])

    try:
        avg_cc = out.split('\n')[-2].split(':')[1]
        return float(avg_cc)
    except IndexError:
        return -1  # CC couldn't be calculated


def get_set_of_classes(malware, folder):
    out_file = os.path.join(folder, config['classes_file'])
    to_ret = set()
    utils.run_java_component(
        config['class_lister'],
        [malware, config['android_sdk'], out_file], 180)
    if os.path.isfile(out_file):
        with open(out_file, 'r') as list_class:
            for li in list_class.readlines():
                to_ret.add(li.strip())
    return to_ret
