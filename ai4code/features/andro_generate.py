#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   andro_generate.py
@Time    :   2021/10/08 11:28:25
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
from androguard.core.analysis import auto
from androguard.decompiler.decompiler import DecompilerDAD
import torch
# import csv
import os.path as osp
import logging.config

from ai4code.features.generate import FeatureGeneration
from ai4code.utils import get_hash_from_file


class AndroGen(auto.DirectoryAndroAnalysis):
    def __init__(self, APKpath, Analyzer, output_dir):
        self.logger = self.get_logger()
        super(AndroGen, self).__init__(APKpath) # self.directory
        self.analyzer = Analyzer if isinstance(Analyzer, list) else [Analyzer]
        self.output_dir = output_dir if isinstance(output_dir, list) else [output_dir]

    def get_logger(self):
        FILE_LOGGING = osp.join(osp.split(osp.realpath(__file__))[0], './resources/logging.conf')
        logging.config.fileConfig(FILE_LOGGING)
        logger = logging.getLogger('fileAndConsole')
        return logger

    def analysis_app(self, log, apkobj, dexobj, adexobj):
        apk_filename = log.filename
        if apk_filename.endswith(".apk"):
            dexobj.set_decompiler(DecompilerDAD(dexobj, adexobj))
            feature_generator = FeatureGeneration()
            for index in range(len(self.analyzer)):
                analyzer = self.analyzer[index]
                self.logger.info("Using Analyzer {}".format(analyzer.__name__))
                feature = feature_generator.get_features(analyzer, ana_obj=[apkobj, dexobj, adexobj], apkpath=apk_filename)
                self.dump_feature(feature, apk_filename, index)

    def finish(self, log):
        # This method can be used to save information in `log`
        # finish is called regardless of a crash, so maybe store the
        # information somewhere
        self.logger.info("#Analysis of {} has finished!".format(log.filename))
        # self.count = self.count + 1 # conflict

    def crash(self, log, why):
        # If some error happens during the analysis, this method will be called
        self.logger.error("Error during analysis of {}: {}".format(log.filename, why))

    def dump_feature(self, feature, apk_filename, index):
        output_dir = self.output_dir[index]
        torch.save(feature, f"{output_dir}/{get_hash_from_file(apk_filename)}.pt")
        
        # record = [self.count, apk_filename]
        # with open(f"{output_dir}/id_apk_mapping.csv", 'a') as f:
        #     writer = csv.writer(f)
        #     writer.writerow(record)


def generate_feature(apk_directory, analyzer, output_dir):
    settings = {
        # The directory `some/directory` should contain some APK files
        "my": AndroGen(apk_directory, analyzer, output_dir),
        # Use the default Logger
        "log": auto.DefaultAndroLog,
        # Use maximum of x threads
        "max_fetcher": 4,
    }
    aa = auto.AndroAuto(settings)
    aa.go()