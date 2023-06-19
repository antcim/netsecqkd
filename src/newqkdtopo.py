import re
from networkx import DiGraph, exception, shortest_path
from superqkdnode import SuperQKDNode
from colorama import Fore
from key_cont import KeyConteiner

class NewQKDTopo():

    def __init__(self, sim_nodes):
        self.sim_nodes = sim_nodes
        self.gen_forward_tables()

    def gen_forward_tables(self):
        graph = DiGraph()
        for n in self.sim_nodes.keys():
            graph.add_node(n)
        
        # print(graph.nodes)
        
        edges = []
        
        for n in graph.nodes:
            for srqkdnode in self.sim_nodes[n].srqkdnodes.values():
                dst = re.search('to (.+?).sender', srqkdnode.sender.name).group(1)
                cc = srqkdnode.sender.cchannels[dst + " to " + n + ".receiver"]
                
                #n_keys = srqkdnode.senderkm.keys
                n_keys = KeyConteiner.keys[srqkdnode.sender.name]
                
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

    def print_tables(self):
        for n in self.sim_nodes:
            print(Fore.LIGHTMAGENTA_EX, "\nROUTING TABLE ", n, Fore.RESET)
            for i, k in self.sim_nodes[n].routing_table.items():
                print("TO ", Fore.LIGHTBLUE_EX, i, Fore.RESET,
                      "Path: ", Fore.LIGHTCYAN_EX, k, Fore.RESET)
    