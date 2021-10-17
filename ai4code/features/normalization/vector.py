#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   vector.py
@Time    :   2021/10/10 19:20:01
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import numpy as np


def get_existence_vector(value_list, reference_list, to_numpy_array=True, handle_undefined=False):
    vector = [1 if p in value_list else 0 for p in reference_list]
    if handle_undefined:
        vector = vector + [1] if sum(vector) == 0 else vector + [0]
    if to_numpy_array:
        vector = np.array(vector)
    return vector


def get_frequency_vector(value_list, reference_list, toSerries=True, divide=False):
    vector = [0] * len(reference_list)
    for v in value_list:
        vector[reference_list.index(v)] += 1
    if toSerries:
        vector = np.array(vector)
    if divide and len(value_list):
        vector = vector / len(value_list)
    return vector


def pad0_numpy_array(arr, target_length):
    """ Pad 0 to the end of the array to reach the target length.
    """
    return np.pad(arr, (0, target_length - len(arr)))

def concatenate_numpy_array(arr_list):
    return np.concatenate(arr_list)