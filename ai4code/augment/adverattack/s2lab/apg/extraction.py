# -*- coding: utf-8 -*-

"""
extraction.py
~~~~~~~~~~~~~

Search, extract, and manage organs for transplantation.

Note that the string representations of features are slightly different depending
on if they're identified by the Drebin feature extractor or by Soot:

    * d_feature: com_s2lab_minactivity_SecondActivity
    * j_feature: com.s2lab.minactivity.SecondActivity

"""
import logging
import pickle
import subprocess
import sys
import uuid
from datetime import datetime
from pprint import pformat
from timeit import default_timer as timer

import numpy as np
import os
import shutil
import tempfile

import apg.drebin as drebin
import apg.inpatients as inpatients
import apg.utils as utils
from apg.settings import config
from apg.utils import yellow, blue, green, red


def search_for_organ(feature, model, search_limit=None):
    """Search for organs among all available apps (in training set).

    Args:
        feature (str): The feature to search for (in Drebin representation).
        model (SVMModel): The target model.
        search_limit (int): The maximum number of apps to return.

    Returns:
        list: Paths for apps in training set containing feature.
    """
    # O(n) but benign weights are sorted so should be quick enough
    feature_index = -1  # Sentinel value
    for f in model.benign_weights:
        if f[0] == feature:
            feature_index = f[1]
            break

    if feature_index == -1:
        logging.error('Catastrophic error, using the wrong model.')
        exit()

    row = model.X_train[:, feature_index]
    present = np.where(row.toarray().T[0] != 0)[0]

    if search_limit:
        present = present[:search_limit]

    return [model.m_train[i]['sample_path'] for i in present]


def contributions(organ, weights_dict, host):
    """Evaluate the compatibility of an organ with the host.

    Args:
        organ (Organ): Organ to be transplanted.
        weights_dict (dict): Mapping of features and weights.
        host (Host): Host receiving the transplant.

    Returns:
        float: The total contribution of the organ's features w.r.t. the host.
    """
    # Check if the same class is contained in host and donor organ
    if host.classes & organ.classes:
        return 0

    # Try to prioritise changes that will remain within benign statistics (IQ range)
    if len(organ.permissions) > 1 or len(organ.classes) > 20:
        return 0

    # Don't consider features already present in the malware
    malware_features = list(host.features.keys())

    # Sum contributions including side effects that aren't already present
    total = sum(weights_dict[f] for f in organ.feature_dict.keys() if
                f in weights_dict.keys() and f not in malware_features)

    return total


def mass_organ_harvest(model, feature_depth, donor_depth):
    """Harvest top organs from donors."""
    logging.info(blue('Attempting to extract the necessary organs...'))
    potential_donors = {}

    # For each new feature to modify, search for potential donors
    for f, _, _ in model.benign_weights[:feature_depth]:
        # Search for all apps that contain the feature needed
        logging.debug(blue(f'Searching for {f} in donors...'))
        donors = search_for_organ(f, model, donor_depth)
        logging.debug(green(f'Found {f} in:\n{pformat(donors)}'))
        potential_donors[f] = donors

    # Get organs for the selected features
    for i, (feature, donor_list) in enumerate(potential_donors.items()):
        for donor_path in donor_list:
            harvest_organ_from_donor(feature, donor_path)


def harvest_organ_from_donor(feature, donor_path):
    """Harvest feature from donor."""
    organ = inpatients.Organ(feature, donor_path)
    os.makedirs(organ.location, exist_ok=True)
    failure_test = os.path.join(organ.location, 'failed')
    pickle_location = os.path.join(organ.location, 'organ.p')

    if os.path.exists(failure_test):
        logging.warning(red('Previously failed') + f' to extract organ for feature {feature} from {donor_path}')
        return None

    if os.path.exists(pickle_location):
        logging.warning(green('Already extracted') + f' organ for feature {feature} from {donor_path}')
        with open(pickle_location, 'rb') as f:
            return pickle.load(f)

    def failure_occurred():
        with open(failure_test, 'wt'):
            pass
        logging.warning('Organ harvest failed.')
        logging.info('Extraction time: {}'.format(
            utils.seconds_to_time(timer() - start)))

    start = timer()
    feature_type, j_feature = drebin.to_j_feature(feature)

    logging.debug(yellow(f'Extracting {j_feature} from {donor_path}...'))

    if not os.path.isfile(donor_path):
        logging.warning(red(f'Donor app not found: {donor_path}'))
        return None

    # Run the extractor!
    try:
        out = extract(donor_path, j_feature, feature_type)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        failure_occurred()
        return None

    out = out.split('\n')

    if 'Dependencies exported and slice' in out[-2]:
        logging.info('Organ harvest successful!')
    elif 'Dependencies exported but no slice' in out[-2]:
        logging.info('Organ harvest successful, but needs vein')
        organ.needs_vein = True
    else:
        logging.info(out[-3:])
        failure_occurred()
        return None

    # Get the list of classes referenced/contained by the slice
    classes_list = os.path.join(organ.location, 'classes.txt')
    with open(classes_list, 'r') as f:
        organ.classes = {x.strip() for x in f.readlines()}

    # Weigh the organ
    logging.debug(f'Evaluating feature {organ.feature}')

    operating_room = tempfile.mkdtemp(dir=config['tmp_dir'])
    template = os.path.join(config['template_path'], 'template.apk')
    template = shutil.copy(template, operating_room)

    logging.debug(blue('Calling the injector...'))
    out = utils.run_java_component(config['template_injector'],
                                   [template,
                                    organ.location,
                                    config['android_sdk']])

    out = out.split('\n')

    if len(out) < 3 or 'Injection done' not in out[-3]:
        failure_occurred()
        return None

    logging.debug("Injection to template completed successfully")

    post_op = os.path.join(operating_room, 'sootOutput', 'template.apk')
    organ.feature_dict = drebin.get_features(post_op)

    count_permissions(organ)
    organ.extraction_time = timer() - start
    logging.info('Extraction time: {}'.format(
        utils.seconds_to_time(organ.extraction_time)))

    with open(pickle_location, 'wb') as f:
        pickle.dump(organ, f)

    return organ


def count_permissions(organ):
    """Count the permissions present in an organ."""
    for feature in organ.feature_dict:
        if "android_permission" in feature:
            organ.permissions.add(feature)
            splits = feature.split("::")[1].replace("_", ".").split(".")
            if len(splits) == 3:
                tmp_p = splits[2]
            elif len(splits) == 4:
                tmp_p = splits[2] + "_" + splits[3]
            elif len(splits) == 5:
                tmp_p = splits[2] + "_" + splits[3] + "_" + splits[4]

            if not tmp_p or tmp_p in utils.dangerous_permissions:
                organ.dangerous_permissions = True


def extract(apk, j_feature, feature_type):
    """Extract feature from given donor apk."""
    activity_types = ('activities', 'Activity')
    feature_type = 'Activity' if feature_type in activity_types else 'URL'

    try:
        out = subprocess.check_output(
            ['java', '-jar', config['extractor'], j_feature,
             apk, feature_type, config['ice_box'],
             config['android_sdk']], stderr=subprocess.PIPE,
            timeout=config['extractor_timeout'])
        out = str(out, 'utf-8')
    except subprocess.TimeoutExpired:
        logging.debug(f'Extractor timed out during {apk}, skipping feature')
        raise
    except subprocess.CalledProcessError as e:
        exception = "\nexit code :{0} \nSTDOUT :{1} \nSTDERROR : {2} ".format(
            e.returncode,
            e.output.decode(sys.getfilesystemencoding()),
            e.stderr.decode(sys.getfilesystemencoding()))
        logfile = 'extraction-exception-{}-{}.log'.format(
            str(uuid.uuid4())[:8],
            datetime.strftime(datetime.now(), '%m-%d--%H:%M'))
        logfile = os.path.join('logs', logfile)
        with open(logfile, 'wt') as f:
            f.write(exception)
        logging.warning(red(f'Exception during extraction [{logfile}]'))
        raise
    return out
