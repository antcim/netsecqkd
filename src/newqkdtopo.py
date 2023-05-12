import json
import re
from sequence.topology.topology import Topology as Topo
from networkx import DiGraph, exception, shortest_path


class NewQKDTopo():

    def __init__(self, sim_nodes):
        self.sim_nodes = sim_nodes
        self.gen_forward_tables()

    def gen_forward_tables(self):
        graph = DiGraph()
        for n in self.sim_nodes.keys():
            graph.add_node(n)
        
        print(graph.nodes)
        
        edges = []
        
        for n in graph.nodes:
            for srqkdnode in self.sim_nodes[n].srqkdnodes:
                dst = re.search('to (.+?).sender', srqkdnode.sender.name).group(1)
                cc = srqkdnode.sender.cchannels[dst + " to " + n + ".receiver"]
                
                n_keys = srqkdnode.senderkm.keys
                
                if len(n_keys) > 0:
                    edges.append((n, dst, {"weight": cc.distance}))
        
        graph.add_edges_from(edges)
        
        for src in graph.nodes:
            for dst in graph.nodes:
                if src == dst:
                    continue
                try:
                    path = shortest_path(graph, source=src, target=dst, weight="weight")
                    self.sim_nodes[src].routing_table[dst] = path
                    
                except exception.NetworkXNoPath:
                    pass
    