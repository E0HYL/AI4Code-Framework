# -*- coding: utf-8 -*-

"""
models.py
~~~~~~~~~

Available target models:
    * SVMModel - a base class for SVM-like models
        - SVM - Standard linear SVM using scikit-learn implementation
        - SecSVM - Secure SVM variant using a PyTorch implementation (based on [1])

[1] Yes, Machine Learning Can Be More Secure! [TDSC 2019]
    -- Demontis, Melis, Biggio, Maiorca, Arp, Rieck, Corona, Giacinto, Roli

"""
import logging
import numpy as np
import os
import pickle
import random
import ujson as json
from collections import OrderedDict
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

import lib.secsvm
from apg.settings import config
from apg.utils import blue, red, yellow


class SVMModel:
    """Base class for SVM-like classifiers."""

    def __init__(self, X_filename, y_filename, meta_filename, num_features=None):
        self.X_filename = X_filename
        self.y_filename = y_filename
        self.meta_filename = meta_filename
        self._num_features = num_features
        self.clf, self.vec = None, None
        self.column_idxs = []
        self.X_train, self.y_train, self.m_train = [], [], []
        self.X_test, self.y_test, self.m_test = [], [], []
        self.feature_weights, self.benign_weights, self.malicious_weights = [], [], []
        self.weight_dict = OrderedDict()

    def generate(self, save=True):
        """Load and fit data for new model."""
        logging.debug(blue('No saved models found, generating new model...'))

        X_train, X_test, y_train, y_test, m_train, m_test, self.vec = load_features(
            self.X_filename, self.y_filename, self.meta_filename, True)

        self.column_idxs = self.perform_feature_selection(X_train, y_train)

        self.X_train = X_train[:, self.column_idxs]
        self.X_test = X_test[:, self.column_idxs]
        self.y_train, self.y_test = y_train, y_test
        self.m_train, self.m_test = m_train, m_test

        self.clf = self.fit(self.X_train, self.y_train)
        features = [self.vec.feature_names_[i] for i in self.column_idxs]

        w = self.get_feature_weights(features)
        self.feature_weights, self.benign_weights, self.malicious_weights = w
        self.weight_dict = OrderedDict(
            (w[0], w[2]) for w in self.feature_weights)

        if save:
            self.save_to_file()

    def dict_to_feature_vector(self, d):
        """Generate feature vector given feature dict."""
        return self.vec.transform(d)[:, self.column_idxs]

    def get_feature_weights(self, feature_names):
        """Return a list of features ordered by weight.

        Each feature has it's own 'weight' learnt by the classifier.
        The sign of the weight determines which class it's associated
        with and the magnitude of the weight describes how influential
        it is in identifying an object as a member of that class.

        Here we get all the weights, associate them with their names and
        their original index (so we can map them back to the feature
        representation of apps later) and sort them from most influential
        benign features (most negative) to most influential malicious
        features (most positive). By default, only negative features
        are returned.

        Args:
            feature_names: An ordered list of feature names corresponding to cols.

        Returns:
            list, list, list: List of weight pairs, benign features, and malicious features.

        """
        assert self.clf.coef_[0].shape[0] == len(feature_names)

        coefs = self.clf.coef_[0]
        weights = list(zip(feature_names, range(len(coefs)), coefs))
        weights = sorted(weights, key=lambda row: row[-1])

        # Ignore 0 weights
        benign = [x for x in weights if x[-1] < 0]
        malicious = [x for x in weights if x[-1] > 0][::-1]
        return weights, benign, malicious

    def perform_feature_selection(self, X_train, y_train):
        """Perform L2-penalty feature selection."""
        if self._num_features is not None:
            logging.info(red('Performing L2-penalty feature selection'))
            selector = LinearSVC(C=1)
            selector.fit(X_train, y_train)

            cols = np.argsort(np.abs(selector.coef_[0]))[::-1]
            cols = cols[:self._num_features]
        else:
            cols = [i for i in range(X_train.shape[1])]
        return cols

    def save_to_file(self):
        with open(self.model_name, 'wb') as f:
            pickle.dump(self, f)


class SVM(SVMModel):
    """Standard linear SVM using scikit-learn implementation."""

    def __init__(self, X_filename, y_filename, meta_filename, num_features=None):
        super().__init__(X_filename, y_filename, meta_filename, num_features)
        self.model_name = self.generate_model_name()

    def fit(self, X_train, y_train):
        logging.debug(blue('Creating model'))
        clf = LinearSVC(C=1)
        clf.fit(X_train, y_train)
        return clf

    def generate_model_name(self):
        model_name = 'svm'
        model_name += '.p' if self._num_features is None else '-f{}.p'.format(self._num_features)
        return os.path.join(config['models'], model_name)


class SecSVM(SVMModel):
    """Secure SVM variant using a PyTorch implementation."""

    def __init__(self, X_filename, y_filename, meta_filename, num_features=None,
                 secsvm_k=0.2, secsvm=False, secsvm_lr=0.0001,
                 secsvm_batchsize=1024, secsvm_nepochs=75, seed_model=None):
        super().__init__(X_filename, y_filename, meta_filename, num_features)
        self._secsvm = secsvm
        self._secsvm_params = {
            'batchsize': secsvm_batchsize,
            'nepochs': secsvm_nepochs,
            'lr': secsvm_lr,
            'k': secsvm_k
        }
        self._seed_model = seed_model
        self.model_name = self.generate_model_name()

    def fit(self, X_train, y_train):
        logging.debug(blue('Creating model'))
        clf = lib.secsvm.SecSVM(lr=self._secsvm_params['lr'],
                                batchsize=self._secsvm_params['batchsize'],
                                n_epochs=self._secsvm_params['nepochs'],
                                K=self._secsvm_params['k'],
                                seed_model=self._seed_model)
        clf.fit(X_train, y_train)
        return clf

    def generate_model_name(self):
        model_name = 'secsvm-k{}-lr{}-bs{}-e{}'.format(
            self._secsvm_params['k'],
            self._secsvm_params['lr'],
            self._secsvm_params['batchsize'],
            self._secsvm_params['nepochs'])
        if self._seed_model is not None:
            model_name += '-seeded'
        model_name += '.p' if self._num_features is None else '-f{}.p'.format(self._num_features)
        return os.path.join(config['models'], model_name)


def load_from_file(model_filename):
    logging.debug(blue(f'Loading model from {model_filename}...'))
    with open(model_filename, 'rb') as f:
        return pickle.load(f)


def load_features(X_filename, y_filename, meta_filename, load_indices=True):
    with open(X_filename, 'rt') as f:
        X = json.load(f)
    #    [o.pop('sha256') for o in X]  # prune the sha, uncomment if needed
    with open(y_filename, 'rt') as f:
        y = json.load(f)
        # y = [x[0] for x in json.load(f)]  # prune the sha, uncomment if needed
    with open(meta_filename, 'rt') as f:
        meta = json.load(f)

    X, y, vec = vectorize(X, y)

    if load_indices:
        logging.info(yellow('Loading indices...'))
        chosen_indices_file = config['indices']
        with open(chosen_indices_file, 'rb') as f:
            train_idxs, test_idxs = pickle.load(f)
    else:
        random_state = random.randint(0, 1000)

        train_idxs, test_idxs = train_test_split(
            range(X.shape[0]),
            stratify=y,
            test_size=0.33,
            random_state=random_state)

        filepath = f'indices-{random_state}.p'
        filepath = os.path.join(config['models'], filepath)
        with open(filepath, 'wb') as f:
            pickle.dump((train_idxs, test_idxs), f)

    X_train = X[train_idxs]
    X_test = X[test_idxs]
    y_train = y[train_idxs]
    y_test = y[test_idxs]
    m_train = [meta[i] for i in train_idxs]
    m_test = [meta[i] for i in test_idxs]

    return X_train, X_test, y_train, y_test, m_train, m_test, vec


def vectorize(X, y):
    vec = DictVectorizer()
    X = vec.fit_transform(X)
    y = np.asarray(y)
    return X, y, vec
