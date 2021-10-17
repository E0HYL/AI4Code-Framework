'''
Author: Yiling He
Date: 2021-03-08 17:33:21
LastEditTime: 2021-03-10 19:38:49
LastEditors: Yiling He
Contact: heyilinge0@gmail.com
Description: 
FilePath: \AI4Code-Framework\ai4code\features\generate.py
'''

class FeatureGeneration(object):
    def __init__(self, input_data=None, code_level="binary", feature_level="bytecode", feature_type="graph"):
        self.input_data = input_data
        
        self.code_level = code_level
        self.feature_level = feature_level
        if code_level != feature_type: # disassamle / decompile
            self.level_transform()
        
        self.feature_type = feature_type

    def level_transform(self):
        pass # return NotImplementedError

    def get_features(self, Analyzer, **kwargs):
        return Analyzer(**kwargs).get_features()
