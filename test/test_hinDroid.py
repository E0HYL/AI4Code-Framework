#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   test_hinDroid.py
@Time    :   2021/10/16 11:21:08
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import unittest
from examples.android_malware_detection import HinDroidAnalyzer

from . import format_print, timer


class TestDrebin(unittest.TestCase):
    def test_xml_bytecode_parser(self):
        ana_obj = HinDroidAnalyzer("/data/e0/AI4Code-Framework/data/apk/raw/hello-world.apk")
        coexist_api_sets, invoke_approaches = ana_obj.analyze_method_APIs()
        format_print(self, f"{ana_obj.filepath}\ncoexist_api_sets of length: {len(coexist_api_sets)}, \ninvoke_approaches of length: {len(invoke_approaches)}")

        print(coexist_api_sets)

    @timer
    def test_drebin_features(self):
        features = HinDroidAnalyzer("/data/e0/AI4Code-Framework/data/apk/raw/hello-world.apk").features
        # format_print(self, features)    