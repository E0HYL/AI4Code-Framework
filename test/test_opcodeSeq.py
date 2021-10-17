#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   test_opcodeSeq.py
@Time    :   2021/10/15 18:57:22
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import unittest
from examples.android_malware_detection import OpcodeSeqAnalyzer

from . import format_print, timer


class TestOpcodeSeq(unittest.TestCase):
    @timer
    def test_opcodeseq_features(self):
        analyzer = OpcodeSeqAnalyzer("/data/e0/AI4Code-Framework/data/apk/raw/hello-world.apk")
        # cg = mamadroid_ana.cg
        # for n in cg.nodes: 
        #     print(str(n.class_name).strip('L').split("/")[:-1])
        #     break
        features = analyzer.get_features()
        print(sum(features))
        format_print(self, features)
