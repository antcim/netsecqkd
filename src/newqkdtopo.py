import json
from sequence.topology.topology import Topology as Topo
from networkx import Graph, dijkstra_path, exception


class NewQKDTopo(Topo):

    QKD_NODE = "QKDNode"

    def __init__(self, filename, sim_nodes):
        self.sim_nodes = sim_nodes
        self.topo_config = json.load(open(filename))
        Topo.__init__(self, filename)

    def _load(self, filename):
        self._generate_forwarding_table()

    def update_tables(self):
        self._generate_forwarding_table()

    def _generate_forwarding_table(self):
        graph = Graph()
        for node in self.topo_config[Topo.ALL_NODE]:
            if node[Topo.TYPE] == self.QKD_NODE:
                graph.add_node(node[Topo.NAME])

        costs = []

        for cc in self.topo_config[Topo.ALL_C_CHANNEL]:
            for n in self.sim_nodes[cc['source']].srqkdnodes:
                if n.sender.name == cc['source'] + " to " + cc['destination'] + ".sender":
                    for rn in self.sim_nodes[cc['destination']].srqkdnodes:
                        if rn.sender.name == cc['destination'] + " to " + cc['source'] + ".sender":
                            if len(n.senderkm.keys) > 0 and len(rn.senderkm.keys) > 0:
                                print(rn.sender.name, n.sender.name)
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
                    self.sim_nodes[src_name].routing_table[dst_name] = path

                except exception.NetworkXNoPath:
                    pass
