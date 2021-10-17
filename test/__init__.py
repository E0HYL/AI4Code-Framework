'''
Author: Yiling He
Date: 2021-03-19 12:35:20
LastEditTime: 2021-03-19 12:36:35
LastEditors: Yiling He
Contact: heyilinge0@gmail.com
Description: 
FilePath: \AI4Code-Framework\test\__init__.py
'''
# make test a package to run unittest
import inspect


def timer(func):
    def func_wrapper(*args,**kwargs):
        from time import time
        time_start = time()
        result = func(*args,**kwargs)
        time_end = time()
        time_spend = time_end - time_start
        print('\n{0} cost time {1} s\n'.format(func.__name__, time_spend))
        return result
    return func_wrapper


def format_print(self, msg, level="INFO"):
    print(f"{level} === Testing [{self.__class__.__name__}]-[{inspect.stack()[1][3]}] ===\n{msg}")