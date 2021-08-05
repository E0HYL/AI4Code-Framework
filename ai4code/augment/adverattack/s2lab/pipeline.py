# -*- coding: utf-8 -*-

"""
pipeline.py
~~~~~~~~~~~

A pipeline to demonstrate the end-to-end problem-space adversarial mutations as presented in
Intriguing Properties of Adversarial ML Attacks in the Problem Space [1].

This implementation targets two classifiers: a standard linear SVM, and SecSVM [2] a modified
secure variant with l_inf regularisation to ensure weights are more evenly distributed.

The pipeline flow can be roughly broken down into four distinct phases:

    1) Prelude to configure logging, output directories, etc
    2) Experiment prep inc. model generation and organ harvesting
    3) Feature-space attack (w/ problem-space constraints) to calculate transformations needed
    4) Problem-space transplantation to generated final adversarial apps

If patient records have already been generated, stage 3) can be skipped by including the command
line flag `--skip-feature-space`.

As the most computationally demanding phase, stage 4) is off by default, it can be invoked by
including the `--transplant` command line flag.

[1] Intriguing Properties of Adversarial ML Attacks in the Problem Space [S&P 2020]
    -- Pierazzi*, Pendlebury*, Cortellazzi, Cavallaro

[2] Yes, Machine Learning Can Be More Secure! [TDSC 2019]
    -- Demontis, Melis, Biggio, Maiorca, Arp, Rieck, Corona, Giacinto, Roli

"""
import argparse
import glob
import logging
import numpy as np
import os
import sklearn
import torch
import torch.multiprocessing as mp
import traceback
import ujson as json
from itertools import repeat
from pprint import pformat

import apg.evasion as evasion
import apg.extraction as extraction
import apg.inpatients as inpatients
import apg.models as models
import apg.utils as utils
from apg.settings import config
from apg.utils import blue, yellow, red, green

mp = torch.multiprocessing.get_context('forkserver')


def main():
    # STAGE 1: PRELUDE #

    args = parse_args()

    # Configure logging and output dirs
    utils.configure_logging(args.run_tag, args.debug)
    output_dir = os.path.join(config['results_dir'], args.run_tag)
    os.makedirs(os.path.join(output_dir, 'success'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'failure'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'estimates'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'adv-features'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'records'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'postop'), exist_ok=True)
    logging.info(yellow(f'Output directory: {output_dir}'))

    # STAGE 2: EXPERIMENT PREP #

    # Load data and create models
    logging.info(blue('Loading data...'))

    if args.secsvm:
        model = models.SecSVM(config['X_dataset'], config['y_dataset'],
                              config['meta'], args.n_features,
                              args.secsvm_k, args.secsvm, args.secsvm_lr,
                              args.secsvm_batchsize, args.secsvm_nepochs,
                              seed_model=args.seed_model)
    else:
        model = models.SVM(config['X_dataset'], config['y_dataset'],
                           config['meta'], args.n_features)

    logging.debug(blue('Fetching model...'))
    if os.path.exists(model.model_name):
        model = models.load_from_file(model.model_name)
    else:
        model.generate()

    logging.info(blue(f'Using classifier:\n{pformat(vars(model.clf))}'))

    # Harvest organs
    if args.harvest:
        extraction.mass_organ_harvest(model, args.organ_depth, args.donor_depth)

    # Find true positive malware
    y_pred = model.clf.predict(model.X_test)
    y_scores = model.clf.decision_function(model.X_test)
    tps = np.where((model.y_test & y_pred) == 1)[0]
    tp_shas = [model.m_test[i]['sha256'] for i in tps]
    tp_hosts = [model.m_test[i]['sample_path'] for i in tps]
    utils.dump_json(tp_shas, output_dir, 'tp_shas.json')
    utils.dump_json(tp_hosts, output_dir, 'tp_hosts.json')

    # Calculate confidence margin
    benign_scores = y_scores[y_scores < 0]
    margin = resolve_confidence_level(args.confidence, benign_scores)
    logging.info(yellow(f'Using confidence attack w/ margin: {margin} ({args.confidence}%)'))

    # Produce some run statistics
    report = calculate_base_metrics(model, y_pred, y_scores, output_dir)
    report['confidence'] = {'confidence': args.confidence, 'margin': margin}
    report['number_of_apps'] = {'train': len(model.y_train),
                                'test': len(model.y_test),
                                'tps': len(tps)}

    logging.info(blue('Performance before attack:\n' + pformat(report)))

    # Log benign features
    benign_feature_names = [x[0] for x in model.benign_weights]
    utils.dump_json(benign_feature_names, output_dir, 'benign-features.json')

    start_time = utils.stamp_start_time(output_dir)
    report['start_time'] = start_time

    # Retry failures from a previous run (some errors are non-deterministic)
    if args.rerun_past_failures:
        failed = glob.glob(os.path.join(output_dir, 'failure', '*.txt'))
        failed = [utils.get_app_name(x) for x in failed]
        tp_hosts = [utils.resolve_sample_filename(x, config['storage_radix']) for x in failed]
        logging.warning(red(f'Rerunning {len(tp_hosts)} failed attempts!'))

    utils.dump_json(report, output_dir, 'run.json', overwrite=False)

    # STAGE 3: FEATURE-SPACE TRANSFORMATIONS (w/ problem-space constraints) #

    # Preload host malware (does more computation upfront to speed up mp)

    if args.preload:
        logging.info(blue('Commencing preload...'))
        with mp.Pool(processes=config['nprocs_preload']) as p:
            p.map(inpatients.Host.load, tp_hosts)

    # Fetch all successfully harvested organs

    logging.info(blue('Fetching harvested organs...'))
    orgs = inpatients.fetch_harvested(benign_feature_names[:args.organ_depth])

    # Feature space evasion (w/ problem space constraints) to generate patient records

    logging.info(blue('Commencing feature space evasion...'))

    if not args.skip_feature_space:
        if not args.serial:
            logging.info(blue('Running attack in parallel...'))
            with mp.Pool(processes=config['nprocs_evasion']) as p:
                p.starmap(evasion.make_evasive, zip(tp_hosts,
                                                    repeat(model),
                                                    repeat(orgs),
                                                    repeat(margin),
                                                    repeat(output_dir)))

        if args.serial:
            logging.info(blue('Running attack in serial...'))
            for tp in tp_hosts:
                evasion.make_evasive(tp, model, orgs, margin, output_dir)

        logging.info(yellow('Patient records generated.'))
        logging.info(blue('Bundling adv features into new dataset...'))

        adv_features = []
        files = sorted(glob.glob(os.path.join(output_dir, 'adv-features', '*.adv.json')))
        for filepath in files:
            with open(filepath, 'rt') as f:
                adv_features.append(json.load(f))
        adv_labels = [1] * len(adv_features)
        adv_meta = [{'sha256': os.path.basename(filepath).split('.')[0]} for filepath in files]

        with open('X.adv.json', 'wt') as f:
            json.dump(adv_features, f)
        with open('y.adv.json', 'wt') as f:
            json.dump(adv_labels, f)
        with open('meta.adv.json', 'wt') as f:
            json.dump(adv_meta, f)

    if not args.transplantation:
        exit()

    # STAGE 4: PROBLEM-SPACE ADVERSARIAL APP GENERATION #

    # Collect all patient records
    records_dir = os.path.join(output_dir, 'records', '*.record.json')
    records = glob.glob(records_dir)

    # Problem-space transplantation for end-to-end adv app generation
    if not args.serial:
        logging.info(blue('Running transplant in parallel...'))
        with mp.Pool(processes=config['nprocs_transplant']) as p:
            p.starmap(transplantation_wrapper, zip(records,
                                                   repeat(model),
                                                   repeat(output_dir),
                                                   repeat(args)))

    if args.serial:
        logging.info(blue('Running transplant in serial...'))
        for record in records:
            transplantation_wrapper(record, model, output_dir, args)

    logging.info(yellow('Transplant completed.'))


def transplantation_wrapper(record, model, output_dir, args):
    """Wrapper to handle and debug errors from the problem space transplantation.

    Args:
        record (str): The path to the precomputed record.
        model (SVMModel): The `SVMModel` for the attack.
        output_dir (str): The root directory of where outputs should be stored.
        args (Namespace): Command line args.

    """
    logging.info('-' * 70)

    sha = utils.get_app_name(record)

    result = os.path.join(output_dir, 'success', f'report-{sha}.apk.json')
    if os.path.exists(result):
        logging.info(green('Already successfully generated!'))
        return

    failed = os.path.join(output_dir, 'failure', f'{sha}.txt')
    if os.path.exists(failed) and not args.rerun_past_failures:
        logging.info(red('Already attempted to generate.'))
        return

    tries = config['tries']
    successful = False
    while not successful and tries > 0:
        try:
            evasion.problem_space_transplant(record, model, output_dir)
            successful = True
        except evasion.RetryableFailure as e:
            tries -= 1

            if tries > 0:
                logging.warning(red('Encountered a random error, retrying...'))
            else:
                logging.error(red('Ran out of tries :O Logging error...'))
                utils.log_failure(record, str(e), output_dir)
        except Exception as e:
            msg = f'Process fell over with: [{e}]: \n{traceback.format_exc()}'
            utils.log_failure(record, msg, output_dir)
            return e
    logging.info(yellow(f'Results in: {output_dir}'))


def resolve_confidence_level(confidence, benign_scores):
    """Resolves a given confidence level w.r.t. a set of benign scores.

    `confidence` corresponds to the percentage of benign scores that should be below
    the confidence margin. Practically, for a value N the attack will continue adding features
    until the adversarial example has a score which is 'more benign' than N% of the known
    benign examples.

    In the implementation, 100 - N is performed to calculate the percentile as the benign
    scores in the experimental models are negative.

    Args:
        confidence: The percentage of benign scores that should be below the confidence margin.
        benign_scores: The sample of benign scores to compute confidence with.

    Returns:
        The target score to resolved at the given confidence level.

    """
    if confidence == 'low':
        return 0
    elif confidence == 'high':
        confidence = 25
    try:
        # perc. inverted b/c benign scores are negative
        return np.abs(np.percentile(benign_scores, 100 - float(confidence)))
    except:
        logging.error(f'Unknown confidence level: {confidence}')


def calculate_base_metrics(model, y_pred, y_scores, output_dir=None):
    """Calculate ROC, F1, Precision and Recall for given scores.

    Args:
        model: `Model` containing `y_test` of ground truth labels aligned with `y_pred` and `y_scores`.
        y_pred: Array of predicted labels, aligned with `y_scores` and `model.y_test`.
        y_scores: Array of predicted scores, aligned with `y_pred` and `model.y_test`.
        output_dir: The directory used for dumping output.

    Returns:
        dict: Model performance stats.

    """
    roc = sklearn.metrics.roc_auc_score(model.y_test, y_scores)
    f1 = sklearn.metrics.f1_score(model.y_test, y_pred)
    precision = sklearn.metrics.precision_score(model.y_test, y_pred)
    recall = sklearn.metrics.recall_score(model.y_test, y_pred)

    if output_dir:
        utils.dump_pickle(y_pred, output_dir, 'y_pred.p')
        utils.dump_pickle(y_scores, output_dir, 'y_scores.p')
        utils.dump_pickle(model.y_test, output_dir, 'y_test.p')

    return {
        'model_performance': {
            'roc': roc,
            'f1': f1,
            'precision': precision,
            'recall': recall,
        }
    }


def parse_args():
    p = argparse.ArgumentParser()

    # Experiment variables
    p.add_argument('-R', '--run-tag', help='An identifier for this experimental setup/run.')
    p.add_argument('--confidence', default="25", help='The confidence level to use (%% of benign within margin).')
    p.add_argument('--n-features', type=int, default=None, help='Number of features to retain in feature selection.')
    p.add_argument('--max-permissions-per-organ', default=5, help='The number of permissions allowed per organ.')
    p.add_argument('--max-permissions-total', default=20, help='The total number of permissions allowed in an app.')

    # Stage toggles
    p.add_argument('-t', '--transplantation', action='store_true', help='Runs physical transplantation if True.')
    p.add_argument('--skip-feature-space', action='store_true',
                   help='Skips generation of patient records and feature estimates.')

    # Performance
    p.add_argument('--preload', action='store_true', help='Preload all host applications before the attack.')
    p.add_argument('--serial', action='store_true', help='Run the pipeline in serial rather than with multiprocessing.')

    # SecSVM hyperparameters
    p.add_argument('--secsvm', action='store_true')
    p.add_argument('--secsvm-k', default="0.25")
    p.add_argument('--secsvm-lr', default=0.0009, type=float)
    p.add_argument('--secsvm-batchsize', default=256, type=int)
    p.add_argument('--secsvm-nepochs', default=10, type=int)
    p.add_argument('--seed_model', default=None)

    # Harvesting options
    p.add_argument('--harvest', action='store_true')
    p.add_argument('--organ-depth', type=int, default=100)
    p.add_argument('--donor-depth', type=int, default=10)

    # Misc
    p.add_argument('-D', '--debug', action='store_true', help='Display log output in console if True.')
    p.add_argument('--rerun-past-failures', action='store_true', help='Rerun all past logged failures.')

    args = p.parse_args()

    if args.secsvm_k == 'inf':
        args.secsvm_k = np.inf
    else:
        args.secsvm_k = float(args.secsvm_k)

    return args


if __name__ == "__main__":
    main()
