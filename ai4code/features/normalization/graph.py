#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   graph.py
@Time    :   2021/10/08 15:53:39
@Author  :   Yiling He
@Version :   1.0
@Contact :   heyilinge0@gmail.com
@License :   (C)Copyright 2021
@Desc    :   None
'''

# here put the import lib
import networkx as nx
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data


class GraphStatistics:
    def __init__(self, nxgraph):
        self.nxgraph = nxgraph

    def get_adj_matrix(self):
        return nx.to_numpy_array(self.nxgraph)

    def get_trans_matrix(self, align_names=None):
        adjacency_matrix = self.get_adj_matrix() 
        # https://networkx.org/documentation/stable/reference/generated/networkx.convert_matrix.to_numpy_array.html The rows and columns are ordered according to the nodes in nodelist. If nodelist is None, then the ordering is produced by G.nodes().
        node_list = list(self.nxgraph.nodes)

        np.seterr(invalid='ignore') # invalid 0 / 0 is allowed
        transition_matrix = np.nan_to_num(adjacency_matrix / adjacency_matrix.sum(axis=1, keepdims=True))
        transition_matrix = pd.DataFrame(transition_matrix, columns=node_list)
        transition_matrix.index = node_list

        if align_names:
            init_features = pd.DataFrame(np.zeros([len(align_names), len(align_names)]), columns=align_names)
            init_features.index = align_names
            _, transition_matrix = init_features.align(transition_matrix, fill_value=0)
            
        return transition_matrix


def get_k_hop_subgraph(whole_graph, center_node, hop, undirected=True):
    return nx.ego_graph(whole_graph, center_node, radius=hop, undirected=undirected)


def convert_graph_data(graph_dict, task="inductive", **kwargs):
    if task == "inductive": # graph classification
        node_attributes = torch.tensor(graph_dict['node_attributes'])
        edge_index = torch.tensor(graph_dict['edge_list'], dtype=torch.long)

        label = graph_dict.get("label")
        if label:
            label = torch.tensor([label], dtype=torch.long)
            return Data(x=node_attributes, y=label, edge_index=edge_index, **kwargs)
        else:
            return Data(x=node_attributes, edge_index=edge_index, **kwargs)

    elif task == "transductive": # node classification # TODO: maybe more attributes
        edge_index = torch.tensor(graph_dict['edge_list'], dtype=torch.long)
        return Data(edge_index=edge_index, **kwargs)