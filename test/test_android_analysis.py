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

class TestAPKAnalysis(unittest.TestCase):
    def setUp(self):
        test_apk_path = "data/apk/raw/TestActivity.apk"
        self.ana_obj = APKAnalyzer(test_apk_path)
        print(f"Analyzing {test_apk_path}")

    def test_call_graph(self):
        g = self.ana_obj.get_call_graph()
        assert isinstance(g, nx.MultiDiGraph)
        print(f"Call graph: {len(g.nodes)} nodes, {len(g.edges)} edges")

    def test_mxs(self):
        d = self.ana_obj.get_mxs()
        print(f"{len(d["androapi"])} Android APIs, {len(d["external"])} external non-Android APIs, {len(d["userdefi"])} methods with code.")
        self.test_mx = d["userdefi"][0]

    def test_method_tokens(self):
        b, t = self.ana_obj.get_method_tokens(self.test_mx)
        print("INFO: Opcode-only mode")
        for i in range(len(b)):
            print(f"{b[i]}   {t[i]}")
        
        b, t = self.ana_obj.get_method_tokens(self.test_mx, operand=True)
        print("INFO: Operand-added mode")
        for i in range(len(b)):
            print(f"{b[i]}   {t[i]}")

    def test_method_cfg(self):
        cfg, inf = self.ana_obj.get_method_cfg(self.test_mx)
        assert isinstance(cfg, nx.MultiDiGraph)
        print(f"{inf}\nCFG: {len(cfg.nodes)} nodes, {len(cfg.edges)} edges")

    def test_method_ast(self):
        ast = self.ana_obj.get_method_ast(self.test_mx)
        print(f"AST: {len(ast)}")

    def test_permissions(self):
        per = self.ana_obj.get_used_permission()
        print(f"{len(per)} used permissions in the APK\n{per}")
