'''
Author: Yiling He
Date: 2021-03-19 12:37:06
LastEditTime: 2021-03-19 14:42:33
LastEditors: Yiling He
Contact: heyilinge0@gmail.com
Description: 
FilePath: \AI4Code-Framework\test\test_android_analysis.py
'''

import unittest
import networkx as nx
from ai4code.features.preprocessing.android import APKAnalyzer

from . import format_print


class TestAPKAnalysis(unittest.TestCase):
    def setUp(self):
        test_apk_path = "/data/e0/AI4Code-Framework/data/apk/raw/hello-world.apk"
        self.ana_obj = APKAnalyzer(test_apk_path)

    def test_call_graph(self):
        g = self.ana_obj.get_call_graph()
        assert isinstance(g, nx.MultiDiGraph)
        format_print(self, f"Call graph: {len(g.nodes)} nodes, {len(g.edges)} edges.")

    def test_mxs(self, debug=True):
        d = self.ana_obj.get_mxs()
        if debug: 
            format_print(self, f"{len(d['androapi'])} Android APIs, {len(d['external'])} external non-Android APIs, {len(d['userdefi'])} methods with code.")
        self.test_mx = d["userdefi"][233]

    def test_method_tokens(self):
        self.test_mxs(debug=False)
        b, t = self.ana_obj.get_method_tokens(self.test_mx)
        format_print(self, "Opcode-only mode")
        for i in range(len(b)):
            print(f"{b[i]}")
        
        b, t = self.ana_obj.get_method_tokens(self.test_mx, operand=True)
        format_print(self, "Operand-added mode")
        for i in range(len(b)):
            print(f"{b[i]}\t{t[i]}")

    def test_method_cfg(self):
        self.test_mxs(debug=False)
        cfg, inf = self.ana_obj.get_method_cfg(self.test_mx)
        assert isinstance(cfg, nx.MultiDiGraph)
        format_print(self, f"{inf}\nCFG: {len(cfg.nodes)} nodes, {len(cfg.edges)} edges")

    def test_method_ast(self):
        self.test_mxs(debug=False)
        ast = self.ana_obj.get_method_ast(self.test_mx)
        format_print(self, f"AST: {ast}")

    def test_permissionss(self):
        per = self.ana_obj.get_used_permissions()
        format_print(self, f"{len(per)} used permissions in the APK\n{per}")

    def test_manifest_permissions(self):
        man_per = self.ana_obj.get_declared_permissions()
        format_print(self, f"{len(man_per)} declared permissions in the APK\n{man_per}")

    def test_manifeat_components(self):
        activities = self.ana_obj.get_xml_components(key='activity')
        format_print(self, f"{len(activities)} Activities: {activities}")
