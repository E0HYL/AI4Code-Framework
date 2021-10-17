#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   literadar.py
@Time    :   2021/10/07 20:53:56
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   Modified from LibRadar (Zachary Marv, 2017). Use Androguard to analyse DEX. Since the method is signiture-based and the original tool use Apktool, the returned TPL library can be lesser. However, the speed is increased and less storage is required.
'''

# here put the import lib
import sys
# import dex_parser
import hashlib
# import zipfile
import json

from .litedextree import Tree
from ._settings import *


class LibRadarLite(object):
    """
    LibRadar
    """
    def __init__(self, apk_path=None, dex_parser=None):
        """
        Init LibRadar instance with apk_path as a basestring.
        Create a Tree for every LibRadar instance. The tree describe 
        the architecture of the apk. Every package is a node.
        :param apk_path: basestring
        """
        self.apk_path = apk_path
        self.dex_parser = dex_parser # AnalyzeAPK: _, d, _
        self.tree = Tree()

        # A list with the .dex file names contained in the apk, for multidex support.
        self.dex_names = []

        # Every element in this array is an instance of Dex Object in dex_parser. This
        # is an array instead of a single element to enable multidex.
        self.dex_objects = []

        """
            Use redis database to exam whether a call is an Android API consumes 27% running time.
            I think it should be replaced by a hash table as the API list could not be modified during the progress.
        """
        self.k_api_v_permission = dict()
        with open(SCRIPT_PATH + "/Data/strict_api.csv", 'r') as api_and_permission:
            for line in api_and_permission:
                api, permission_with_colon = line.split(",")
                permissions = permission_with_colon[:-2].split(":")
                # delete the last empty one
                permission_list = list()
                for permission in permissions:
                    if permission != "":
                        permission_list.append(permission)
                self.k_api_v_permission[api] = permission_list
        """
        invoke_file = open(SCRIPT_PATH +"/Data/IntermediateData/invokeFormat.txt", 'r')
        self.invokes = set()
        for line in invoke_file:
            self.invokes.add(line[:-1])
        """

    def __del__(self):
        # Delete dex file
        if CLEAN_WORKSPACE >= 3:
            for dex_name in self.dex_names:
                os.remove(dex_name)
                os.removedirs(os.path.dirname(dex_name))

    # def unzip(self):
    #     # If it is a valid file
    #     if not os.path.isfile(self.apk_path):
    #         logger.error("%s is not a valid file." % self.apk_path)
    #         raise AssertionError
    #     # If it is a apk file
    #     if len(self.apk_path) <= 4 or self.apk_path[-4:] != ".apk":
    #         logger.error("%s is not a apk file.")
    #         raise AssertionError
    #     # Get SHA256
    #     self.hex_sha256 = self.get_sha256()
    #     # Unzip
    #     zf = zipfile.ZipFile(self.apk_path, mode='r')

    #     # Save all the .dex files contained in the apk into the Decompiled directory and save
    #     # the .dex file names into the dex_names array.
    #     try:
    #         self.dex_names.append(zf.extract("classes.dex", SCRIPT_PATH + "/Data/Decompiled/%s" % self.hex_sha256))

    #         # Enable multidex support. If this apk has only a .dex file, then the dex_names array
    #         # will contain a single element.
    #         basename = "classes%d.dex"

    #         ## Little hack to let Python2 work without much trouble
    #         try:
    #             x_range = xrange(2, sys.maxint)
    #         except:
    #             x_range = range(2, sys.maxsize)

    #         for i in x_range:
    #             self.dex_names.append(zf.extract(basename % i, SCRIPT_PATH + "/Data/Decompiled/%s" % self.hex_sha256))

    #     except KeyError:
    #         pass

    #     return self.dex_names

    def get_dex_parsers(self):
        from androguard.misc import AnalyzeAPK
        _, dexs, _ = AnalyzeAPK(self.apk_path)
        self.dex_parser = dexs

    def get_sha256(self):
        if not os.path.isfile(self.apk_path):
            logger.critical("file path %s is not a file" % self.apk_path)
            raise AssertionError
        file_sha256 = hashlib.sha256()
        f = open(self.apk_path, 'rb')
        while True:
            block = f.read(4096)
            if not block:
                break
            file_sha256.update(block)
        f.close()
        file_sha256_value = file_sha256.hexdigest()
        logger.debug("APK %s's MD5 is %s" % (self.apk_path, file_sha256_value))
        return file_sha256_value

    # def get_api_list(self, dex_obj, dex_method, api_list, permission_list):
    #     if dex_method.dexCode is None:
    #         return
    #     offset = 0
    #     insns_size = dex_method.dexCode.insnsSize * 4

    #     while offset < insns_size:
    #         op_code = int(dex_method.dexCode.insns[int(offset):int(offset + 2)], 16)
    #         decoded_instruction = dex_parser.dexDecodeInstruction(dex_obj, dex_method.dexCode, offset)
    #         smali_code = decoded_instruction.smaliCode
    #         if smali_code is None:
    #             logger.warning("smali code is None.")
    #             continue
    #         # Next Instruction.
    #         offset += decoded_instruction.length
    #         if smali_code == 'nop':
    #             break
    #         # 4 invokes from 0x6e to 0x72
    #         if 0x6e <= op_code <= 0x72:
    #             if decoded_instruction.getApi in self.k_api_v_permission:
    #                 api_list.append(decoded_instruction.getApi)
    #                 for permission in self.k_api_v_permission[decoded_instruction.getApi]:
    #                     permission_list.add(permission)
    #     return
    
    def get_api_list(self, class_analysis, api_list, permission_list):
        class_method_list = class_analysis.get_methods()
        package_name = "/".join(str(class_analysis.name).split("/")[:2])
        # print(package_name)
        for method in class_method_list:
            logger.debug("Analyzing method %s" % method.name)
            for instruction in method.get_instructions():
                if instruction.get_op_value() == 0x00: break # "nop"

                if instruction.get_name().startswith('invoke'):
                    operands_output = instruction.get_output()
                    api_ind = operands_output.find(", L") + 2
                    api = operands_output[api_ind:].split("(")[0]                    
                    if api.startswith(package_name) or api.startswith('Ljava/lang/') or (not api.startswith('L')):
                        continue #
                    api_list.append(api)
        
        for api in api_list:
            logger.debug(f"Invoke API: {api}")
            if api in self.k_api_v_permission:
                permission = self.k_api_v_permission[api]
                if permission:
                    permission_list.append(permission)
                # # print("API found in k_api_v_permission")
                # for permission in self.k_api_v_permission[api]: 
                #     permission_list.add(permission)
                #     # print(permission_list)

    # def extract_class(self, dex_obj, dex_class_def_obj):
    #     class_sha256 = hashlib.sha256()
    #     # API List
    #     #   a list for basestring
    #     api_list = list()
    #     permission_list = set()
    #     # direct methods
    #     last_method_index = 0

    #     for k in range(len(dex_class_def_obj.directMethods)):
    #         current_method_index = last_method_index + dex_class_def_obj.directMethods[k].methodIdx
    #         last_method_index = current_method_index
    #         self.get_api_list(dex_obj, dex_class_def_obj.directMethods[k], api_list=api_list, permission_list=permission_list)
    #     # virtual methods
    #     last_method_index = 0
    #     for k in range(len(dex_class_def_obj.virtualMethods)):
    #         current_method_index = last_method_index + dex_class_def_obj.virtualMethods[k].methodIdx
    #         last_method_index = current_method_index
    #         self.get_api_list(dex_obj, dex_class_def_obj.virtualMethods[k], api_list=api_list, permission_list=permission_list)
        
    #     # Use sort to pass the tree construction stage.
    #     # In this case, we could only use a stack to create the package features.
    #     api_list.sort()
    #     for api in api_list:
    #         class_sha256.update(api.encode())
    #     if not IGNORE_ZERO_API_FILES or len(api_list) != 0:
    #         pass
    #     return len(api_list), class_sha256.hexdigest(), class_sha256.hexdigest(), sorted(list(permission_list))
        
    def extract_class(self, dex_class_def_obj):
        class_sha256 = hashlib.sha256()
        # API List
        #   a list for basestring
        api_list = list()
        permission_list = list()

        self.get_api_list(dex_class_def_obj, api_list=api_list, permission_list=permission_list)
        
        # Use sort to pass the tree construction stage.
        # In this case, we could only use a stack to create the package features.
        api_list.sort()
        for api in api_list:
            class_sha256.update(api.encode())
        if not IGNORE_ZERO_API_FILES or len(api_list) != 0:
            pass
        return api_list, class_sha256.hexdigest(), class_sha256.hexdigest(), permission_list

    # def extract_dex(self):

    #     for dex_name in self.dex_names:
    #         # Log Start
    #         logger.debug("Extracting %s" % dex_name)
    #         # Validate existing
    #         if not os.path.isfile(dex_name):
    #             logger.error("%s is not a file" % dex_name)
    #             return -1
    #         # Create a Dex object for each dex file contained in the apk.
    #         current_dex = dex_parser.DexFile(dex_name)
    #         self.dex_objects.append(current_dex)
    #         for dex_class_def_obj in current_dex.dexClassDefList:
    #             weight, raw_sha256, hex_sha256, permission_list = self.extract_class(dex_obj=current_dex, dex_class_def_obj=dex_class_def_obj)
    #             class_name = current_dex.getDexTypeId(dex_class_def_obj.classIdx)
    #             """
    #             I got many \x01 here before the class name.
    #                 such as '\x01Lcom/vungle/publisher/inject'
    #             don't know exactly but could use code below to deal with it.
    #             """
    #             if class_name[0] is not 'L':
    #                 l_index = class_name.find('L')

    #                 if l_index == '-1':
    #                     continue

    #                 class_name = class_name[l_index:]

    #             if IGNORE_ZERO_API_FILES and weight == 0:
    #                 continue

    #             self.tree.insert(package_name=class_name, weight=weight, sha256=raw_sha256, permission_list=permission_list)
    #     return 0

    def extract_dex(self):
        self.dex_parser = self.dex_parser if isinstance(self.dex_parser, list) else [self.dex_parser]
        for dex in self.dex_parser:
            # Log Start
            logger.debug("Extracting DEX %s" % dex)

            for dex_class_def_obj in dex.get_classes(): # a list of :class:`ClassDefItem` objects
                logger.debug("Analyzing class %s" % dex_class_def_obj)
                apilist, raw_sha256, hex_sha256, permission_list = self.extract_class(dex_class_def_obj=dex_class_def_obj)
                weight = len(apilist)
                class_name = dex_class_def_obj.name

                if IGNORE_ZERO_API_FILES and weight == 0:
                    continue

                self.tree.insert(package_name=class_name, weight=weight, sha256=raw_sha256, permission_list=permission_list)
                # print(class_name, weight, raw_sha256, permission_list)
                # print(apilist)
        return 0

    def analyse(self):
        """
        Main function for LibRadar Object.
        :return: None
        """
        # Step 1: Unzip APK file, only extract the dex files.
        # self.unzip()
        if self.dex_parser is None:
            self.get_dex_parsers()
        # Step 2: Extract Dex and insert package-level info into Tree
        # self.extract_dex()
        self.extract_dex()
        # Step 3: post-order traverse the tree, calculate every package's sha256 value.
        self.tree.cal_sha256()

    def compare(self):
        self.analyse()
        # Step 4: pre-order traverse the tree, calculate every node's match degree (similarity).
        self.tree.match()
        # Init res for step 5 & 6
        res = list()
        # Step 5: traverse the tree, find out all the libraries.
        self.tree.get_lib(res)
        # Step 6: traverse the tree, find potential libraries that has not been tagged.
        self.tree.find_untagged(res)
        return res


def get_tpl_pkgs(apk_path=None, d=None):
    """Return Dict of all the TPL packages and the permission list of the sensitive API included in the package.
    """
    lrd = LibRadarLite(apk_path=apk_path, dex_parser=d)
    res = lrd.compare()
    pkgs = {}
    for i in res:
        pkgs[i['Package']] = i['Permission']
    return pkgs


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("LiteRadar only takes 1 argument.")
        print("Usage:")
        print("    $ python literadar.py example.apk")
        exit(1)
    iron_apk_path = sys.argv[1]
    lrd = LibRadarLite(iron_apk_path)
    res = lrd.compare()
    print(json.dumps(res, indent=4, sort_keys=True))
