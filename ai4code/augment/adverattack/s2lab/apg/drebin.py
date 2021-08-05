# -*- coding: utf-8 -*-

"""
drebin.py
~~~~~~~~~

A set of helper functions for interacting with the Drebin [1] feature extractor.


[1] DREBIN: Effective and Explainable Detection of Android Malware
    in Your Pocket [NDSS 2014] -- Arp et. al

"""
import glob
import logging
import subprocess

import os
import shutil
import tempfile
import ujson as json

from apg.settings import config
from apg.utils import blue


def get_features(app_path):
    """Extract Drebin feature vectors from the app.

    Args:
        app_path: The app to extract features from.

    Returns:
        dict: The extracted feature vector in dictionary form.

    """
    app_path = os.path.abspath(app_path)
    output_dir = tempfile.mkdtemp(dir=config['tmp_dir'])

    cmd = ['python2', './drebin.py', app_path, output_dir]
    location = config['feature_extractor']

    logging.info(blue('Running command') + f' @ \'{location}\': {" ".join(cmd)}')
    subprocess.call(cmd, cwd=location)

    results_file = glob.glob(output_dir + '/results/*.json')[0]
    logging.debug('Extractor results in: {}'.format(results_file))
    with open(results_file, 'rt') as f:
        results = json.load(f)
    shutil.rmtree(output_dir)
    results.pop('sha256')  # Ensure hash isn't included in features
    return results


def to_j_feature(full_d_feature):
    feature_type, d_feature = full_d_feature.split('::')
    return feature_type, d_feature.replace('_', '.')
