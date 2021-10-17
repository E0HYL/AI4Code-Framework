#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   test_mamadroid.py
@Time    :   2021/10/02 20:36:30
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import unittest
from examples.android_malware_detection import MaMaDroidAnalyzer

from . import format_print, timer


class TestMamadroid(unittest.TestCase):
    @timer
    def test_mamadroid_features(self):
        mamadroid_ana = MaMaDroidAnalyzer("/data/e0/AI4Code-Framework/data/apk/raw/hello-world.apk")
        # cg = mamadroid_ana.cg
        # for n in cg.nodes: 
        #     print(str(n.class_name).strip('L').split("/")[:-1])
        #     break
        features = mamadroid_ana.get_features()
        format_print(self, features)
        """ Value_counts of target nodes from the source node `self-defined`
        java.lang                 18    
        self-defined               6
        android.support.design     4
        android.support.v7.app     3
        android.view               2
        """
        src_ = features.loc['self-defined', :]
        print(src_[src_!=0.0])