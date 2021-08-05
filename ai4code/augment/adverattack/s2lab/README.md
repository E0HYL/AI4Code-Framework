# Adversarial Program Generation

This repository contains the code for performing constrained white-box adversarial problem-space attacks for Android.

Further details can be found in the paper _"Intriguing Properties of Adversarial ML Attacks in the Problem Space"_ by F. Pierazzi\*, F. Pendlebury\*, J. Cortellazzi, and L. Cavallaro (IEEE S&P 2020). Check out https://s2lab.kcl.ac.uk/projects/intriguing/ for up-to-date information on the project and links to presentation recordings.

If you end up building on this research or code as part of a project or publication, please include a reference to the IEEE S&P paper:

```
@inproceedings{pierazzi2020problemspace,
    author = {F. Pierazzi and F. Pendlebury and J. Cortellazzi and L. Cavallaro},
    booktitle = {IEEE Symposium on Security and Privacy},
    title = {Intriguing Properties of Adversarial ML Attacks in the Problem Space},
    year = {2020},
    volume = {},
    issn = {2375-1207},
    pages = {1308-1325},
    doi = {10.1109/SP40000.2020.00073},
    url = {https://doi.ieeecomputersociety.org/10.1109/SP40000.2020.00073},
    publisher = {IEEE Computer Society},
}
```

## Getting Started

This pipeline consists of a number of moving parts and has recently been disentangled from our research infrastructure so while we've done our best to include all the details for setting up a new deployment, the process is fairly involved and we apologise if something is absent! 

If it looks like there's a step missing, please let us know and we can try to help (and update this procedure) :) 

### Installation

Before getting started we recommend setting up a Python 3 (>= 3.6.7) virtual environment. Additionally for the Java components, ensure you have installed a Java SDK >= 1.8.0 (corresponding to Java 8). 

1. Install any packages listed in `requirements.txt` using `pip`. 

2. Download the Android SDK with build tools (this can be a pain to do outside of Android Studio, but SO questions like https://stackoverflow.com/questions/17963508/how-to-install-android-sdk-build-tools-on-the-command-line may help).

3. Download a tool for extracting the Drebin features - [you can access a copy of what we use here](https://www.dropbox.com/s/ztthwf6ub4mxxc9/feature-extractor.tar.gz?dl=0). Ensure your environment includes dependencies for the tool, in particular that you have a copy of the AAPT (Android Asset Packaging Tool) and that everything is set up correctly in the tool's `settings.py` file. 

### Configuration

The next step is to fill out configuration in `apg.settings.py`. 

Due to the multiple moving parts, we try to resolve most paths to their absolute form to reduce slip-ups. 

* `_project_path`: The absolute path to the root folder of the project (e.g., `/home/s2lab/apg-release`)
* `_components_path`: The absolute path of the folder containing the compiled Java components (e.g., `home/s2lab/apg-release/java-components/build`)

The helper functions `_project()` and `_components()` can be used to resolve files in these directories given their relative paths. 

Experiment settings: 

* `models`: The path where the models will be saved and loaded from (e.g., `_project('data/models')`)
* `X_dataset`: The features to use (e.g., `_project('data/features/data-X.json')`)
* `y_dataset`: The ground truth to use (e.g., `_project('data/features/data-y.json')`)
* `meta`: A list of dictionaries containing meta information for each example (such as `sha256` to identify the APK and `sample_path` to tell the pipeline where to find the original app) (e.g., `_project('data/features/data-meta.json')`)
* `indices`: A pickled tuple of indices `(train_indices, test_indices)` to define the dataset split. If `use_indices` of `models.load_features` is `False`, a random split will be used and this file isn't necessary (e.g., `_project('data/models/indices.p')`) 

Paths to each of the Java components: 

* `extractor`: The path to the compiled extractor (e.g., `_components('extractor.jar`)
* `injector`: The path to the compiled injector (e.g., `_components('injector.jar'`)
* `template_injector`: The path to the compiled template injector (e.g., `_components('templateinjector.jar')`)
* `cc_calculator`: The path to the compiled CC calculator (e.g., `_components('cccalculator.jar`)
* `class_lister`: The path to the compiled class lister (e.g., `_components('classlister.jar')`))
* `extractor_timeout`: How long to wait for the injector process before timing out, in seconds (e.g., `300`))
* `cc_calculator_timeout`: How long to wait for the CC calculator process before timing out, in seconds (e.g., `600`))

And other components: 

* `android_sdk`: The path to the Android SDK with build tools (e.g., `/opt/android-sdk-linux`)
* `template_path`: The path to the minimal APK to use for template injection (e.g., `_project('template')`)
* `mined_slices`: The path to store and retrieve adapted veins (e.g., `_project('mined_slices')`)
* `opaque_pred`: The path to retrieve opaque predicate Jimple from (e.g., `_project(opaque-preds/sootOutput')`)
* `resigner`: The path to the APK (re)signer (e.g., `_project('apk-signer.jar')`)
* `feature_extractor`: The path to the Drebin feature extractor (e.g., `/home/s2lab/feature-extractor`)

Storage areas for generated bits-and-bobs:

* `tmp_dir`: A temp directory needed for various things such as directories wherein transplantation takes place (e.g., `/media/nas/tmp`)
* `ice_box`: The directory to store all the harvested organs (e.g., `/media/nas/apg/ice-box`)
* `results_dir`: The root directory where results for all runs should be stored (e.g., `/media/nas/apg/apg-results`)
* `goodware_location`: The root directory where all goodware are stored (e.g., `/media/nas/datasets/android/samples/`). Apps are assumed to be stored with filenames of the form [appSha256].apk. 
* `storage_radix`: The radix used is goodware apps are stored with one (e.g., `0` for `[goodware_location]/00A36346.apk` or `3` for `[goodware_location]/0/0/A/00A36346.apk`)

And some miscellaneous options mainly regarding performance:

* `tries`: The number of times to retry errors that are (usually) caused by some non-determinism or Soot bug (must be >= `1` for anything to happen).  
* `nprocs_preload`: The number of processors to use when preloading hosts (e.g., `8`).
* `nprocs_evasion`: The number of processors to use when generating evasive apps (e.g., `12`). 
* `nprocs_transplant`: The number of processors to use when performing problem-space transplantations (e.g., `8`). 

### Usage

As well as the configuration settings, there are a number of command line arguments:
```
$ python3 pipeline.py -h
usage: pipeline.py [-h] [-R RUN_TAG] [--confidence CONFIDENCE]
                   [--n-features N_FEATURES]
                   [--max-permissions-per-organ MAX_PERMISSIONS_PER_ORGAN]
                   [--max-permissions-total MAX_PERMISSIONS_TOTAL] [-t]
                   [--skip-feature-space] [--preload] [--serial] [--secsvm]
                   [--secsvm-k SECSVM_K] [--secsvm-lr SECSVM_LR]
                   [--secsvm-batchsize SECSVM_BATCHSIZE]
                   [--secsvm-nepochs SECSVM_NEPOCHS] [--seed_model SEED_MODEL]
                   [--harvest] [--organ-depth ORGAN_DEPTH]
                   [--donor-depth DONOR_DEPTH] [-D] [--rerun-past-failures]
...
```
(see `pipeline.py` or run `python3 pipeline.py -h` for detailed help.)

#### Harvesting phase 

The initial stage is to populate the ice-box with extracted organs. This will usually involve adding the `--harvest` flag to whatever command you're planning to use to run the main experiment. To reduce computation, the harvesting phase will skip over any organs already stored in the `ice_box`, even if they were harvested for a different run. 

The main arguments are: 

* `--harvest`: Include to trigger the harvesting phase. 
* `--organ-depth`: The number of features to retrieve organs for (e.g., the top N benign features). 
* `--donor-depth`: The number of donors (goodware apps) to try and retrieve each organ from. 

Examples: 

```
python3 pipeline.py -D \
    -R HARVEST \
    --organ-depth 200 \
    --donor-depth 5 \
    --harvest
```

```
python3 pipeline.py -D \
    -R HARVEST \
    --organ-depth 500 \
    --donor-depth 1 \
    --n-features 40000 \
    --secsvm
```

#### Generation phase 

The generation phase can be considered as two stages. In the first stage the attack is performed as it would be in the feature-space only, _except_ only transformations that can be completed using the organs in the ice-box are considered. Practically, harvested organs are ordered by their total benign contribution, and selected one by one until the host app would be misclassified with the required confidence margin. 

For each true-positive malware considered, the main outputs of this phase are a feature vector corresponding to the expected adversarial malware, and a 'patient record'. 

Note that for your purposes, the adversarial feature vectors (representing adversarial examples generated with problem-space constraints) may be sufficient. We've divided the pipeline up in this way so that you can avoid the more computationally intensive end-to-end generation of APKs if you wish.   

Examples: 
```
python3 pipeline.py -D \
  -R EXAMPLE-25 \
  --confidence 25 \
  --n-features 10000 \
  --preload 
```

```
python3 pipeline.py -D \
  -R EXAMPLE-25 \
  --confidence high \
  --n-features 10000 \
  --preload \
  --secsvm \
  --secsvm-k 0.2 \
  --secsvm-lr 0.0001 \
  --secsvm-nepochs 75 \
  --secsvm-batchsize 1024 \
  --seed_model '/home/trustypatches/apg-testing/data/models/svm-f10000.p' 
```

The main arguments are: 

* `run-tag` (`R`): A tag to group all runs with the same setting (used for the output directory also).
* `confidence`: The confidence margin for the attack. Practically, for a value N the attack will continue adding features until the adversarial example has a score which is 'more benign' than N% of the known benign examples (also `low` for `0` and `high` for `25`). 
* `n-features`: How many top-n features to retain in feature selection. 
* `preload`: Whether to preload all the hosts before the attack which moves a lot of the computation up front (strongly recommended).

For the full generation of problem-space examples, the patient records generated in the first stage are used to tell the pipeline which 'operations' to perform:

```python3
patient_record = {
    'host': 'malware', # the path to the malware host receiving the transplant 
    'organs': [organ1, organ2, organ3], # the paths to each of the organs to transplant 
    ... # some other info 
}
```

For this phase you can include the command line args: 
* `--transplant`: Include to trigger the problem-space transplantation phase. 
* `--skip-feature-space`: Include to skip the first stage if patient records have already been generated. 

## Java Components 

The Python wrappers in the pipeline will handle running the Java components as subprocesses, but we also document their command line args here for completeness and to aid debugging.

### Core Modules

#### Injector

This module is one of the two core modules of the framework and it is able to inject a set of custom features into a target APK.

```
java -jar injector.jar \
    <malware_apk> \
    <path_to_jimple_files> \
    <output_folder> \
    <android_sdk_path> \
    <path_to_mined_slices> \
    <path_to_opaques> \
    <path_to_permissions> \
    <cc_threshold>
``` 

* `malware_apk`: The target apk 
* `path_to_jimple_files`: The folder containing the slices database
* `output_folder`: Where to output the final apk
* `android_sdk_path`: Path to the local Android SDK
* `path_to_mined_slices`: Folder containing the dataset of mined slices
* `path_to_opaques`: Folder containing the opaque predicates used during the injection
* `path_to_permissions`: Permission to add to the target apk
* `cc_threshold`: Threshold used during the candidate class search for the injection

#### Extractor:

This module is the other core module of the framework and it is able to extract a feature and the set of dependencies from a target apk.

```
java -jar extractor.jar \
    <feature> \
    <path_to_goodware> \
    <feature_type> \
    <path_for_save_jimples>
```

* `feature`: The feature that we are interested to extract 
* `path_to_goodware`: The path to the target APK from which we want to extract the feature from
* `feature_type`: The type of feature to extract (e.g., URL, Activity)
* `path_to_save_jimples`: The output folder

### Utility modules:

#### Template Injector:

This is simplified version of the injector which is used to inject organs into a minimal app and 'weigh' their contributions.

```
java -jar templateinjector.jar \
    <malware_apk> \
    <path_to_jimple_files> \
    <android_sdk_path> 
```

It takes less arguments than the full injector because it doesn't inject an adapted vein or opaque predicate.

#### CC Calculator:

This module given an input apk will return the AVG CC of the target apk.

```
java -jar cccalculator.jar \
    <malware_apk> \
    <android_sdk_path> \
    <export_cc_distribution> 
```

* `malware_apk`: The apk to analyze
* `android_sdk_path`: Path to the Android SDK
* `export_cc_distribution`: The location to export a json report

#### Class Counter:

This module returns the number of classes in a target apk.

```
java -jar classlister.jar \
    <goodware_apk> \
    <Android_sdk_path>
```

* `goodware_apk`: The apk to analyze
* `android_sdk_path`: Path to the Android SDK

## Licensing 

Code in this repository is covered by two separate licenses. All items in the `java-components` directory are released under a permissive BSD 3-Clause License. 

For ethical considerations, _the remainder of the repository_ is covered by a similar license but which also restricts the use of the code to academic purposes and which specifically prohibits commercial applications. 

>  Any redistribution or use of this software must be limited to the purposes of non-commercial scientific research or 
non-commercial education. Any other use, in particular any use for commercial purposes, is prohibited. This includes, 
without limitation, incorporation in a commercial product, use in a commercial service, or production of other 
artefacts for commercial purposes.