"""
Author: Yiling He
Date: 2021-03-09 14:04:04
LastEditTime: 2021-03-09 14:04:05
LastEditors: Yiling He
Contact: heyilinge0@gmail.com
Description: 
FilePath: \AI4Code-Framework\ai4code\features\preprocessing\android.py
"""


from androguard.misc import AnalyzeAPK
from androguard.core.bytecodes.dvm_types import Kind, Operand
from androguard.decompiler.dad.decompile import DvMethod
from androguard.decompiler.dad.graph import construct
from androguard.core.bytecodes.apk import APK
import networkx as nx
import hashlib
from collections import defaultdict
from ai4code.features.preprocessing import Analyzer
from ai4code.features.preprocessing.androguard_literadar import get_tpl_pkgs


class APKAnalyzer(Analyzer):
    def __init__(self, apkpath, ana_obj=None):
        """
        `a` an APK object: all information about the APK, like package name, permissions, the AndroidManifest.xml or its resources.
        `d` an array of DalvikVMFormat object: the DEX file found inside the APK file, get classes, methods or strings from the DEX file
        `dx` an Analysis object: support multiple DEX files, also call graphs and crossreferences (XREFs) for each method, class, field and string
        """

        super(APKAnalyzer, self).__init__(apkpath)
        if ana_obj is None:
            self.a, self.d, self.dx = AnalyzeAPK(apkpath)
        else:
            self.a, self.d, self.dx = ana_obj

    def get_call_graph(self):
        """ Get call graph of the APK

        Returns:
            nx.MultiDiGraph: NetworkX class
        """        
        
        return self.dx.get_call_graph()

    def get_mxs(self):
        """ All MethodAnalysis object for the APK, divided into three types

        Returns:
            defaultdict: {"androapi": [mx1, ...], "external": [mx2, ...], "userdefi": [mx3, ...]}
        """        
        
        mxs = defaultdict(list) # default: 0
        for method in self.dx.get_methods():
            if method.is_android_api():
                mxs["androapi"].append(method)
            elif method.is_external():
                mxs["external"].append(method)
            else:
                mxs["userdefi"].append(method)
        return mxs

    def get_method_tokens(self, mx, operand=False):
        """ Get tokens and corresponding types

        Args:
            mx (androguard.core.analysis.analysis.MethodAnalysis): same type as call graph node
            operand (bool): keep operands or not

        Returns:
            list: bytecodes sequence
            list: type of each bytecode # opcode: -1, see operand type in `instruction_format()`
        """        

        assert mx.is_external() == False
        m = mx.get_method()
        bytecode_seq = []
        types = []
        for ins in m.get_instructions():
            opcode, operands = instruction_format(ins)
            types.append(-1)
            bytecode_seq.append(opcode)
            if operand:
                types.extend([i[0] for i in operands])
                bytecode_seq.extend([i[1] for i in operands])

        if operand:
            return bytecode_seq, types
        else:
            return bytecode_seq

    def get_method_cfg(self, mx):   
        """Go through all basic blocks of a method and create the CFG (rewrite `androguard.core.bytecodes.method2dot`)

        Args:
            mx (androguard.core.analysis.analysis.MethodAnalysis): same type as call graph node
            
        Returns:
            nx.MultiDiGraph: NetworkX class
                `node` block_hash: {
                    "opcode": [opc_ins1, opc_ins2, ...], 
                    "operands": [[(type1.1, value1.1), (type1.2, value1.2), ...], [(type2.1, value2.1), ...], ...]
                    # operand type: see instruction_format()
                    }
                `edge` (src_block, dst_block): {
                    "type": , # see edge_types
                    "note":
                }
            defaultdict: general information of the method (name, reg, param, return) # default to empty string ''
        """

        assert mx.is_external() == False
        method = mx.get_method()
        CFG = nx.MultiDiGraph()
        edge_types = {
            "true_branch": 0,
            "false_branch": 1,
            "default_branch": 2,
            "jump_branch": 3,
            "exception_branch": 4,
            "payload_branch": 5 # pseudo instruction holding the switch payload
        }

        # This is used as a seed to create unique hashes for the nodes
        sha256 = hashlib.sha256(
            mx.get_method().get_class_name() + mx.get_method().get_name() + mx.get_method().get_descriptor()).digest()

        new_links = []

        # Go through all basic blocks and create the CFG
        for basic_block in mx.basic_blocks:
            ins_idx = basic_block.start
            block_id = hashlib.md5(sha256 + basic_block.get_name()).hexdigest()

            # node attr: bytecode of a block
            block_opcode = []
            block_operand = []
            for instruction in basic_block.get_instructions():
                if instruction.get_op_value() in (0x2b, 0x2c):
                    new_links.append((basic_block, ins_idx, instruction.get_ref_off() * 2 + ins_idx))
                elif instruction.get_op_value() == 0x26:
                    new_links.append((basic_block, ins_idx, instruction.get_ref_off() * 2 + ins_idx))
                
                opcode, ins_operands = instruction_format(instruction)
                block_opcode.append(opcode)
                block_operand.append(ins_operands)

                ins_idx += instruction.get_length()
            CFG.add_nodes_from([(block_id, {"opcode": block_opcode, "operands": block_operand})])

            # Block edges type treatment (conditional branchs edge_types)
            val = edge_types["true_branch"]
            if len(basic_block.childs) > 1:
                val = edge_types["false_branch"]
            elif len(basic_block.childs) == 1:
                val = edge_types["jump_branch"]

            values = None
            # The last instruction is important and still set from the loop
            if instruction.get_op_value() in (0x2b, 0x2c) and len(basic_block.childs) > 1:
                val = edge_types["default_branch"]
                values = ["default"]
                values.extend(basic_block.get_special_ins(ins_idx - instruction.get_length()).get_values())

            # updating edges
            for DVMBasicMethodBlockChild in basic_block.childs:
                label_edge = ""

                if values:
                    label_edge = values.pop(0)

                child_id = hashlib.md5(sha256 + DVMBasicMethodBlockChild[-1].get_name()).hexdigest()
                CFG.add_edges_from([(block_id, child_id, {"type": val, "note": label_edge})])

                # type switch
                if val == edge_types["false_branch"]:
                    val = edge_types["true_branch"]
                elif val == edge_types["default_branch"]:
                    val = edge_types["true_branch"]

            exception_analysis = basic_block.get_exception_analysis()
            if exception_analysis:
                for exception_elem in exception_analysis.exceptions:
                    exception_block = exception_elem[-1]
                    if exception_block:
                        exception_id = hashlib.md5(sha256 + exception_block.get_name()).hexdigest()
                        CFG.add_edges_from([(block_id, child_id, {"type": edge_types["exception_branch"], "note": exception_elem[0]})])

        for link in new_links:
            basic_block = link[0]
            DVMBasicMethodBlockChild = mx.basic_blocks.get_basic_block(link[2])

            if DVMBasicMethodBlockChild:
                block_id = hashlib.md5(sha256 + basic_block.get_name()).hexdigest()
                child_id = hashlib.md5(sha256 + DVMBasicMethodBlockChild.get_name()).hexdigest()

                CFG.add_edges_from([(block_id, child_id, {"type": edge_types["payload_branch"], "note": (link[1], link[2])})])

        # general information of the method
        method_info = defaultdict(str) # default: ''
        method_info["name"] = method.full_name

        method_information = method.get_information()
        if method_information:
            method_info["local_reg_num"] = method_information["registers"][1] + 1 # (start, end): (0, local_reg_num-1)
            if "params" in method_information:
                method_info["params"] = method_information["params"] # [(reg_1, type_1), (reg_2, type_2), ..., (reg_n, type_n)]
            method_info["return"] = method_information["return"] # type

        return CFG, method_info

    def get_method_cfg_primary(self, mx):
        """Returns the primary CFG in Androguard

        Args:
            mx (androguard.core.analysis.analysis.MethodAnalysis)

        Returns:
            Graph: https://github.com/androguard/androguard/blob/8d091cbb309c0c50bf239f805cc1e0931b8dcddc/androguard/decompiler/dad/graph.py#L28
        """

        dvm_instance = DvMethod(mx)
        graph = construct(dvm_instance.start_block, dvm_instance.var_to_name, dvm_instance.exceptions)
        return graph

    def get_method_ast(self, mx):
        """ Abstract syntax trees (AST) of a method

        Args:
            mx (androguard.core.analysis.analysis.MethodAnalysis): same type as call graph node

        Returns:
            dict: abstract syntax trees
        """   

        assert mx.is_external() == False
        dv = DvMethod(self.dx.get_method(mx.get_method()))
        dv.process(doAST=True)
        
        # TODO: prase ast dict to graph
        return dv.get_ast()

    def get_used_permissions(self):
        """ Get APIs who require permissions, using the mapping from Axplorer

        Returns:
            list of tuples: [(mx1, [per1.1, ...]), (mx2, [per2.1, ...])]
        """        

        return list(self.dx.get_permissions(self.a.get_effective_target_sdk_version()))

    def get_declared_permissions(self):
        """ Get permissions declared in the Manifest

        Returns:
            set of the permissions
        """
        return self.a.get_permissions()

    def get_xml_components(self, key): # 'service', 'receiver', 'provider', 'hardware', 'intent-filter'
        """ Get components from the Manifest
        
        Args:
            key: type of the component

        Returns: 
            list of component names
        """

        apk_xml = APK(self.filepath)
        if key == 'activity':
            return apk_xml.get_activities()
        elif key == 'service':
            return apk_xml.get_services()
        elif key == 'receiver':
            return apk_xml.get_receivers()
        elif key == 'provider':
            return apk_xml.get_providers()
        elif key == 'hardware': # indicated by 'uses-feature', e.g., ['android.hardware.touchscreen', 'android.hardware.touchscreen.multitouch', 'android.hardware.touchscreen.multitouch.distinct']
            return apk_xml.get_features()
        elif key == 'intent-filter':
            return apk_xml # need futher analysis
        else:
            raise ValueError("Unknown xml component: %s" % key)

    def get_all_intent_filters(self):
        """ Traverse all 'activity', 'service', 'receiver' to get their intent-filters
        
        Returns:
            list of intent-filters
        """
        
        filters = []
        parser = self.get_xml_components(key='intent-filter')

        for itemtype in ['activity', 'service', 'receiver']:
            for component_name in self.get_xml_components(key=itemtype):
                filter_action = parser.get_intent_filters(itemtype, component_name)['action']
                filters += filter_action
        return filters

    def get_tpl_pkgs(self):
        return get_tpl_pkgs(d=self.d)


def instruction_format(instruction):
    """ Format an instruction
    operand type: REGISTER = 0, LITERAL = 1, RAW = 2, OFFSET = 3, METH = 4, STRING = 5, FIELD = 6, TYPE = 7

    Args:
        instruction (androguard.core.bytecodes.dvm.Instruction)

    Returns:
        str: opcode (mnemonic)
        list of tuples: [(operand1_type, operand1), ...]
    """    

    opcode = instruction.get_name()
    operands = instruction.get_operands()
    # operands: list of tuples, where the first element indicates the type
    ins_operands = []
    for operand in operands:
        if operand[0] & Operand.KIND:
            operand_type = len(Operand) - 1 + (operand[0] - Operand.KIND) # METH = 4, STRING = 5, FIELD = 6, TYPE = 7
            ins_operands.append((operand_type, operand[2]))
        else:
            operand_type = operand[0].value # REGISTER = 0, LITERAL = 1, RAW = 2, OFFSET = 3
            ins_operands.append((operand_type, operand[1]))
    
    return opcode, operands
