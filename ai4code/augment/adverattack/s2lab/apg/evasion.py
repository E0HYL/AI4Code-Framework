# -*- coding: utf-8 -*-

"""
evasion.py
~~~~~~~~~~

Transform a malware into an evasive adversarial variant constrained by available
problem-space transformations.

"""
import logging
import pickle
import time
from collections import Counter
from pprint import pformat
from timeit import default_timer as timer

import copy
import numpy as np
import os
import scipy
import shutil
import ujson as json

import apg.drebin as drebin
import apg.extraction as extraction
import apg.inpatients as inpatients
import apg.utils as utils
from apg.settings import config
from apg.utils import yellow, green, blue


def make_evasive(malware, model, orgs, margin, output_dir):
    """Generate an adversarial feature vector and patient record based on available organs.

    Two important outputs are generated by this function:

        * Adversarial feature vector:
            A mutated feature vector that will be misclassified by the target model. This feature vector
            is constrained by the available features (and associated side effect features) and acts as an
            estimation to the features induced by the end-to-end problem-space transformation.
        * Patient record:
            A record of the host and organs expected to cause misclassification. These records are used to
            later on to tell the transplantation functions which physical mutations to perform.

    Args:
        malware (str): The path to the malware to be made evasive.
        model (SVMModel): The model to target.
        orgs (list): List of harvested `Organs` ready for transplant.
        margin (float): The confidence margin to use during the attack.
        output_dir (str): The root of the output directory in which to dump generated artifacts.

    """
    logging.info(blue('Loading host malware...'))
    host = inpatients.Host.load(malware)
    logging.info(green(f'Host {host.name} loaded!'))

    # Setup output file paths
    records_dir = os.path.join(output_dir, 'records')
    record_name = f'{host.name}.record.json'

    features_dir = os.path.join(output_dir, 'adv-features')
    features_name = f'{host.name}.adv.json'

    # Check if adv feature (and record - implicit) has already been created
    if os.path.exists(os.path.join(features_dir, features_name)):
        return

    # Calculate the minimum perturbation needed for misclassification
    X_initial_vector = model.dict_to_feature_vector(host.features)

    initial_score = model.clf.decision_function(X_initial_vector)[0]
    predicted_class = model.clf.predict(X_initial_vector)

    if predicted_class == 0:
        msg = f'Initial target {host.name} is not predicted as malware! (weird)'
        raise Exception(msg)

    logging.info(blue('Calculating target score and target perturbation...'))
    target_perturbation = np.abs(initial_score - -margin)
    logging.info(f'{initial_score} - {target_perturbation} = -{margin}')

    # Mutate and save feature vector based on available organs

    logging.info(blue('Generating viable adversarial vector...'))

    orgs_to_consider = copy.deepcopy(orgs)
    l1_original = sum(host.features.values())
    to_inject = {}

    def confidence_too_low(x):
        score = model.clf.decision_function(model.dict_to_feature_vector(x))[0]
        return score > -margin

    while confidence_too_low(host.features):
        vals = [extraction.contributions(x, model.weight_dict, host) for x in orgs_to_consider]

        # Sort organs by largest (negative) contribution
        sorted_orgs = [None] * len(orgs_to_consider)
        for i, j in enumerate(np.argsort(vals)):
            sorted_orgs[i] = orgs_to_consider[j]
        orgs_to_consider = sorted_orgs

        next_best = orgs_to_consider.pop(0)

        to_inject[next_best.feature] = next_best
        host.features.update(next_best.feature_dict)

    l1_adv = sum(host.features.values())

    new_vector = model.dict_to_feature_vector(host.features)
    new_score = model.clf.decision_function(new_vector)[0]
    logging.info(yellow(f'New score: {new_score} (< -{margin})'))

    utils.dump_json(host.features, features_dir, features_name)

    # Save patient record

    patient_record = {
        'host': malware,
        'organs': [org.location for org in to_inject.values()],
        'score': float(initial_score),
        'margin': margin,
        'target_perturbation': float(target_perturbation),
        'organ_contribution': float(new_score - initial_score),
        'distortion_l1': l1_adv - l1_original
    }

    patient_record.update(get_counts(host.features))
    utils.dump_json(patient_record, records_dir, record_name)


def problem_space_transplant(record, model, output_dir):
    """Perform transplant described in patient record.

    Args:
        record (str): The path to the patient record detailing which organs are to be transplanted.
        model (SVMModel): The target model.
        output_dir (str): The root of the output directory in which to dump generated artifacts.

    """
    start = timer()

    with open(record, 'r') as f:
        record = json.load(f)

    # Load malware host
    host = inpatients.Host.load(record['host'])
    logging.info(green(f'Host {host.name} ready for operation!'))

    # Load organs
    to_inject = {}
    for filename in record['organs']:
        with open(filename + '/organ.p', 'rb') as f:
            o = pickle.load(f)
        to_inject[o.feature] = o

    X_original = model.dict_to_feature_vector(host.features)

    # Calculate surplus permissions
    surplus_permissions = set()
    for organ in to_inject.values():
        surplus_permissions.update(organ.permissions)
    surplus_permissions -= set(host.permissions)

    # Create dictionary to store ongoing statistics
    results = {}

    # Necessary features are known and extracted, perform inverse mapping
    logging.debug(green('Synthesizing adversarial evader...'))
    logging.info(green('Adding the following features:'))
    logging.info(green('\n' + '\n'.join(to_inject.keys())))
    logging.info(yellow('Including the following side-effects:'))
    side_effects = set()
    for organ in to_inject.values():
        organ_effects = {x for x in organ.feature_dict.keys()
                         if x != organ.feature}
        side_effects.update(organ_effects)
    logging.info(yellow('\n' + pformat(side_effects)))

    # These permissions are the ones needed for the new organs
    # They'll get added to the host manifest by the injector
    perm_file = os.path.join(host.tmpdname, 'permissions.txt')

    logging.info(
        'Injection requires ' + yellow(len(surplus_permissions)) + ' surplus permission(s): ' +
        yellow(surplus_permissions))
    logging.info(f'Writing to perm_file: {perm_file}...')

    with open(perm_file, "wt") as f:
        for p in surplus_permissions:
            splits = p.split("::")[1].replace("_", ".").split(".")
            if len(splits) == 3:
                tmp_p = p.split("::")[1].replace("_", ".")
            elif len(splits) == 4:
                tmp_p = splits[0] + "." + splits[1] + "." + \
                        splits[2] + "_" + splits[3]
            elif len(splits) == 5:
                tmp_p = splits[0] + "." + splits[1] + "." + \
                        splits[2] + "_" + splits[3] + "_" + \
                        splits[4]
            else:
                tmp_p = ''
            f.write(tmp_p)

    # Create the string for input to the injector pointing to the single gadget folders
    apks = ','.join([o.location for o in to_inject.values()])
    logging.debug(f'Final organs to inplant: {apks}')

    # Move files into a working directory and perform injection
    now = time.time()
    # perm_file = perm_file if len(surplus_permissions) > 0 else None
    post_op_host, final_avg_cc, classes_final = transplant(host, apks, perm_file)
    post = time.time()

    results['time_injection'] = int(post - now)

    # Handle error results
    if 'error' in post_op_host:
        msg = f"Error occurred during injection {post_op_host}"
        shutil.rmtree(host.tmpdname)
        raise RetryableFailure(msg)

    elif 'EXCEPTION' in post_op_host:
        logging.debug(" : " + post_op_host)
        logging.debug("Something went wrong during injection, see error.\n")
        if 'SootUtility.initSoot' in post_op_host:
            logging.debug("Soot exception for reading app")

        shutil.rmtree(host.tmpdname)
        msg = "Something went wrong during injection, see error above."
        raise Exception(msg)

    # Resign the modified APK (will overwrite the unsigned one)
    resign(post_op_host)
    logging.debug("Final apk signed")

    # Verify the features of the modified APK
    logging.debug('Verifying adversarial features...')
    new_adv_dict = drebin.get_features(post_op_host)
    new_adv_dict = soot_filter(host.features, new_adv_dict, side_effects)

    X_new_adv = model.dict_to_feature_vector(new_adv_dict)

    # X | Verify output prediction
    score = model.clf.decision_function(X_new_adv)[0]
    out = model.clf.predict(X_new_adv)[0]
    logging.debug('Final score: {}'.format(score))
    logging.debug('Final class prediction {}'.format(out))

    if out != 0:
        msg = f'Generated program not predicted as malware'
        raise RetryableFailure(msg)

    intended_features = set(to_inject.keys())
    obtained_features = set(new_adv_dict.keys())

    if all(x in obtained_features for x in intended_features):
        ret_message = "All intended features are present!"
        results['status'] = 'Success'
        logging.info(green(ret_message))
    else:
        ret_message = "Something went wrong, couldn't find all the features."
        total_time = utils.seconds_to_time(timer() - start)
        print('Time taken: {}'.format(total_time))
        raise RetryableFailure(ret_message)

    # Compute and output results/statistics

    size_final = os.path.getsize(post_op_host)
    end = timer()

    total_time = end - start

    X_ori_arr = X_original.toarray()[0]
    X_adv_arr = X_new_adv.toarray()[0]

    norm = scipy.linalg.norm
    distortion_l0 = abs(norm(X_ori_arr, 0) - norm(X_adv_arr, 0))
    distortion_l1 = abs(norm(X_ori_arr, 1) - norm(X_adv_arr, 1))
    distortion_l2 = abs(norm(X_ori_arr, 2) - norm(X_adv_arr, 2))
    distortion_linf = abs(norm(X_ori_arr, np.inf) - norm(X_adv_arr, np.inf))

    results['distortion_l0'] = distortion_l0
    results['distortion_l1'] = distortion_l1
    results['distortion_l2'] = distortion_l2
    results['distortion_linf'] = distortion_linf

    harvest_times = [o.extraction_time for o in to_inject.values()]

    results['post_op_host'] = post_op_host
    results['feature_stats_start'] = get_counts(host.features)
    results['feature_stats_final'] = get_counts(new_adv_dict)
    results['cc_start'] = host.avg_cc
    results['cc_final'] = final_avg_cc
    results['cc_difference'] = final_avg_cc - host.avg_cc
    results['classes_start'] = len(host.classes)
    results['classes_final'] = classes_final
    results['classes_difference'] = classes_final - len(host.classes)
    results['size_start'] = host.size
    results['size_final'] = size_final
    results['size_difference'] = size_final - host.size
    results['time_start'] = start
    results['time_end'] = end
    results['time_taken'] = total_time
    results['time_organ_extractions'] = harvest_times
    results['time_taken_with_harvesting'] = total_time + sum(harvest_times)

    report_path = os.path.join(output_dir, 'success', f'report-{host.name}.json')
    logging.info(f'Writing report to {report_path}')
    with open(report_path, 'wt') as f:
        json.dump(results, f, indent=2)

    # If a previous attempt had failed, remove error log
    failure_path = os.path.join(output_dir, 'failure', f'{host.name}.txt')
    if os.path.exists(failure_path):
        os.remove(failure_path)

    # Move post op from temp folder to output dir
    shutil.move(post_op_host, os.path.join(output_dir, 'postop', host.name + '.adv'))

    logging.info(blue('Time taken: {}'.format(utils.seconds_to_time(total_time))))
    logging.info(blue('Final size is  {} bytes - size increased by {} bytes'.format(
        size_final, size_final - host.size)))
    logging.info(blue('Final CC of the malware {} - CC difference {} '.format(
        final_avg_cc, final_avg_cc - host.avg_cc)))
    return


def transplant(host, apks, perm_file=None):
    """Transplant a set of organs into a host malware.

    Args:
        host (Host): The host malware set to receive the transplanted organs.
        apks (str): Comma-separated list of donor APKs in the ice-box from which to transplant from.
        perm_file (str): The path to the permissions file of the host.

    Returns:
        (str, int, int): The path to the post-op host, its avg cc, its number of classes.
    """
    output_location = os.path.join(host.tmpdname, 'postop')

    host_path = os.path.join(host.tmpdname, host.name)
    os.makedirs(output_location, exist_ok=True)

    args = [host_path, apks,
            output_location,
            config['android_sdk'],
            config['mined_slices'],
            config['opaque_pred']]

    if perm_file:
        args.append(perm_file)

    logging.info(blue('Performing organ transplantation!'))
    out = utils.run_java_component(config['injector'], args)

    out = out.split('\n')

    if not out or len(out) < 3 or 'Injection done' not in out[-2]:
        msg = "An error occurred during injection {} + {}: {}".format(
            host_path, apks, str(out))
        raise Exception(msg)

    logging.debug(green("Injection completed successfully"))

    avg_cc = out[-4].split(':')[1]
    classes = out[-3].split(' ')[-1]

    return os.path.join(output_location, host.name), int(avg_cc), int(classes)


def resign(app_path):
    """Resign the apk."""
    utils.run_java_component(config['resigner'], ['--overwrite', '-a', app_path])


def get_counts(d):
    """Count features aggregated by type."""
    counter = Counter([x.split('::')[0] for x in d.keys()])
    try:
        del counter['_id']
        del counter['sha256']
    except KeyError:
        pass

    keys = ['intents', 'activities', 'providers', 'urls', 'interesting_calls',
            'api_permissions', 'app_permissions', 'api_calls', 's_and_r']

    return {k: counter.get(k, 0) for k in keys}


def soot_filter(X_original, X_generated, side_effects):
    """Remove erroneous features caused by Soot libraries.

    A bug in our version of Soot means that some additional libraries are added to the app
    even if they're explicitly blacklisted. The exact libraries will depend on your version of
    Soot and Java classpath.

    Here we filter out any features that were not present in either the original malware or any
    of the injected organs as these have been added erroneously by Soot.

    Args:
        X_original: The original malware features.
        X_generated: The generated adversarial malware object.
        side_effects: The set of side effect features that were added.

    Returns:
        Modified X_generated with erroneous features removed.

    """
    added_by_soot = {
        'api_calls::android/media/AudioRecord',
        'api_calls::android/telephony/TelephonyManager;->getSubscriberId',
        'api_calls::java/net/DatagramSocket',
        'api_calls::java/net/MulticastSocket',
        'api_calls::java/net/NetworkInterface',
        'api_permissions::android_permission_READ_PHONE_STATE',
        'api_permissions::android_permission_RECORD_AUDIO',
        'interesting_calls::getCellLocation',
        'interesting_calls::getCellSignalStrength',
        'interesting_calls::getDeviceId',
        'interesting_calls::getNetworkCountryIso',
        'interesting_calls::getSimCountryIso',
        'interesting_calls::getSubscriberId',
        'interesting_calls::getWifiState',
        'interesting_calls::sendSMS',
        'interesting_calls::setWifiEnabled',
        'urls::http://apache_org/xml/features/validation/dynamic',
        'urls::http://apache_org/xml/features/validation/schema',
        'urls::http://java_sun_com/jaxp/xpath/dom',
        'urls::http://javax_xml_XMLConstants/feature/secure-processing',
        'urls::http://javax_xml_transform_dom_DOMResult/feature',
        'urls::http://javax_xml_transform_dom_DOMSource/feature',
        'urls::http://javax_xml_transform_sax_SAXResult/feature',
        'urls::http://javax_xml_transform_sax_SAXSource/feature',
        'urls::http://javax_xml_transform_sax_SAXTransformerFactory/feature',
        'urls::http://javax_xml_transform_sax_SAXTransformerFactory/feature/xmlfilter',
        'urls::http://javax_xml_transform_stream_StreamResult/feature',
        'urls::http://javax_xml_transform_stream_StreamSource/feature',
        'urls::http://relaxng_org/ns/structure/1_0',
        'urls::http://www_w3_org/2001/XMLSchema',
        'urls::http://www_w3_org/2001/XMLSchema-instance',
        'urls::http://www_w3_org/2003/11/xpath-datatypes',
        'urls::http://www_w3_org/TR/REC-xml',
        'urls::http://www_w3_org/xmlns/2000/',
        'urls::http://xml_org/sax/features/namespace-prefixes',
        'urls::http://xml_org/sax/features/namespaces',
        'urls::http://xml_org/sax/features/validation',
        'urls::http://xml_org/sax/properties/declaration-handler',
        'urls::http://xml_org/sax/properties/lexical-handler',
        'urls::http://xmlpull_org/v1/doc/features_html'}

    for k in added_by_soot:
        if k in X_generated and k not in X_original and k not in side_effects:
            del X_generated[k]

    return X_generated


class RetryableFailure(Exception):
    def __init__(self, message):
        super().__init__(message)