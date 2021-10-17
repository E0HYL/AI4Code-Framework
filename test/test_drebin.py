#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   test_drebin.py
@Time    :   2021/10/03 14:27:51
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import unittest
from examples.android_malware_detection import DrebinAnalyzer

from . import format_print, timer


class TestDrebin(unittest.TestCase):
    def test_xml_bytecode_parser(self):
        drebin_ana = DrebinAnalyzer("/data/e0/AI4Code-Framework/data/apk/raw/hello-world.apk", informative=False, dex_only=False)
        format_print(self, f"Activities: {drebin_ana.activity}, \nService: {drebin_ana.service}, \nReceivers: {drebin_ana.receiver}, \nProviders: {drebin_ana.provider}, \nHardware: {drebin_ana.hardware}, \nIntent-filters: {drebin_ana.intent_filter}. \nRequested Permissions: {drebin_ana.declared_permissions}, \nUsed Permissions: {drebin_ana.used_permissions}. \nRestricted APIs: {drebin_ana.restricted_apis}, \nSuspicious APIs: {drebin_ana.suspicious_apis}. \nNetwork Addresses: {drebin_ana.urldomain}")
        print("Restricted APIs:", len(drebin_ana.restricted_apis), "Permission:", len(drebin_ana.used_permissions), "Suspicious APIs:", len(drebin_ana.suspicious_apis))

    @timer
    def test_drebin_features(self):
        features = DrebinAnalyzer("/data/e0/AI4Code-Framework/data/apk/raw/hello-world.apk").features
        print("Restricted APIs:", sum(features[:3810]), "Permission:", sum(features[3810:3810+231]), "Suspicious APIs:", sum(features[3810+231:]))
        format_print(self, features)    