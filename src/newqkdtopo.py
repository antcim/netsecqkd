import json
from sequence.topology.topology import Topology as Topo
from networkx import Graph, dijkstra_path, exception


class NewQKDTopo(Topo):

    QKD_NODE = "QKDNode"

    def __init__(self, filename, sim_nodes):
        self.sim_nodes = sim_nodes
        Topo.__init__(self, filename)
     
    def _load(self, filename):
        topo_config = json.load(open(filename))
        self._generate_forwarding_table(topo_config, self.sim_nodes)
    
    def _generate_forwarding_table(self, config, sim_nodes):
        graph = Graph()
        for node in config[Topo.ALL_NODE]:
            if node[Topo.TYPE] == self.QKD_NODE:
                graph.add_node(node[Topo.NAME])

        costs = []
        for cc in config[Topo.ALL_C_CHANNEL]:
            
            entry = (cc['source'], cc['destination'],
                        {"price": cc['distance']})
            costs.append(entry)

        graph.add_edges_from(costs)

        for src_name in graph.nodes:
            for dst_name in graph.nodes:
                if src_name == dst_name:
                    continue
                try:
                    path = dijkstra_path(graph, src_name, dst_name)
                    sim_nodes[src_name].routing_table[dst_name] = path
                    
                except exception.NetworkXNoPath:
                    pass

