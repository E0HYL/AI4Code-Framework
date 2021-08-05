# -*- coding: utf-8 -*-

"""
settings.py
~~~~~~~~~~~

Configuration options for the pipeline.

"""
import os

# The absolute path to the root folder of this project
_project_path = ''
# The absolute path of the folder containing compiled Java components
_components_path = ''


def _project(base):
    return os.path.join(_project_path, base)


def _components(base):
    return os.path.join(_components_path, base)


config = {
    # Experiment settings
    'models': _project('data/models/'),
    'X_dataset': _project('data/features/apg-X.json'),
    'y_dataset': _project('data/features/apg-y.json'),
    'meta': _project('data/features/apg-meta.json'),
    'indices': _project(''),  # only needed if using fixed indices
    # Java components
    'extractor': _components('extractor.jar'),
    'injector': _components('injector.jar'),
    'template_injector': _components('templateinjector.jar'),
    'cc_calculator': _components('cccalculator.jar'),
    'class_lister': _components('classlister.jar'),
    'classes_file': _project('all_classes.txt'),
    'extractor_timeout': 300,
    'cc_calculator_timeout': 600,
    # Other necessary components
    'android_sdk': '',
    'template_path': _project('template'),
    'mined_slices': _project('mined-slices'),
    'opaque_pred': _project('opaque-preds/sootOutput'),
    'resigner': _project('apk-signer.jar'),
    'feature_extractor': '',
    # Storage for generated bits-and-bobs
    'tmp_dir': '',
    'ice_box': '',
    'results_dir': '',
    'goodware_location': '',
    'storage_radix': 0,  # Use if apps are stored with a radix (e.g., radix 3: root/0/0/A/00A384545.apk)
    # Miscellaneous options
    'tries': 1,
    'nprocs_preload': 8,
    'nprocs_evasion': 12,
    'nprocs_transplant': 8
}
