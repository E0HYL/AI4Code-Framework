#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   _file.py
@Time    :   2021/10/16 15:03:51
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
from pathlib import Path
import logging
import os
import time


def get_hash_from_file(filename):
    return Path(filename).stem


class myFileHandler(logging.FileHandler):
    def __init__(self, path, fileName, mode):
        r = str(int(time.time()))
        a, b = fileName.split('.')
        fileName = a + r + '.' + b
        if not os.path.exists(path):
            os.makedirs(path)
        super(myFileHandler,self).__init__(os.path.join(path, fileName), mode)