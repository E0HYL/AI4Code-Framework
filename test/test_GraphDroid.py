#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   test_GraphDroid.py
@Time    :   2021/10/12 14:42:28
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import unittest
from examples.android_malware_detection import GraphDroidAnalyzer


class TestGraphDroid(unittest.TestCase):
    def test_GraphDroid(self):
        snippet_subgraphs = GraphDroidAnalyzer(apkpath="/data/e0/APKDataset/MyDataset/malware/2015/91EFCE54A379D67A60B08E4DD3F822E98F21392A4C4995D45AABA130ADC077ED.apk").features
        for snippet in snippet_subgraphs:
            print(snippet)