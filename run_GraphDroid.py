#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   run_GraphDroid.py
@Time    :   2021/10/14 16:13:49
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import os
from ai4code.features import generate_feature
from examples.android_malware_detection import GraphDroidAnalyzer, MaMaDroidAnalyzer, OpcodeSeqAnalyzer, DrebinAnalyzer, HinDroidAnalyzer


def batch_analysis(analyzers, categories, years, apk_dir="/data/e0/APKDataset/MyDataset"):
    for c in categories:
        for y in years:
            current_apk_dir = f"{apk_dir}/{c}/{y}/"
            output_dirs = [f"processed/{analyzer.__name__}/{c}/{y}" for analyzer in analyzers]
            for o in output_dirs:
                if not os.path.exists(o):
                    os.makedirs(o)
            generate_feature(current_apk_dir, analyzers, output_dirs)


if __name__ == '__main__':
    # analyzer = DrebinAnalyzer
    # category = 'malware'
    # for year in range(2015, 2020):
    #     apk_dir = f"/data/e0/APKDataset/MyDataset/{category}/{year}/"
    #     output_dir = f"processed/{analyzer.__name__}/{category}/{year}"
    #     if not os.path.exists(output_dir):
    #         os.makedirs(output_dir)
    #     generate_feature(apk_dir, analyzer, output_dir=output_dir)

    analyzers = [GraphDroidAnalyzer, MaMaDroidAnalyzer, OpcodeSeqAnalyzer, DrebinAnalyzer, HinDroidAnalyzer]
    categories = ['malware'] # , 'benign'
    years = range(2015, 2020)
    batch_analysis(analyzers, categories, years)