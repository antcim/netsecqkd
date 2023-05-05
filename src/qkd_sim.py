from ipywidgets import interact
from matplotlib import pyplot as plt
import time

from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.topology.qkd_topo import QKDTopo

import networkx as nx
import json

from netparser import netparse


class KeyManager():
    def __init__(self, timeline, keysize, num_keys):
        self.timeline = timeline
        self.lower_protocols = []
        self.keysize = keysize
        self.num_keys = num_keys
        self.keys = []
        self.times = []

    def send_request(self):
        for p in self.lower_protocols:
            # interface for BB84 to generate key
            p.push(self.keysize, self.num_keys)

    def pop(self, info):  # interface for BB84 to return generated keys
        self.keys.append(info)
        self.times.append(self.timeline.now() * 1e-9)


def genNetwork(filepath):
    # generate random graph
    G = nx.random_lobster(10, 0.2, 0.25)
    # JSON representation
    jsonG = nx.node_link_data(G)
    with open(filepath, 'w') as f:
        json.dump(jsonG, f, ensure_ascii=False)


def readConfig(filepath):
    return QKDTopo(filepath)

def runQKD(network, keysize):
    NUM_KEYS = 25
    PRINT_KEYS = False

    tl = network.get_timeline()

    # for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
    #     print("channels for {}".format(node.name))
    #     node.set_seed(i)
    #     for key in node.qchannels.keys():
    #         print(node.qchannels[key].name)

    n1 = network.get_nodes_by_type(QKDTopo.QKD_NODE)[0]
    n2 = network.get_nodes_by_type(QKDTopo.QKD_NODE)[1]
    n1.set_seed(0)
    n2.set_seed(1)
    pair_bb84_protocols(n1.protocol_stack[0], n2.protocol_stack[0])

    cc0 = network.get_cchannels()[0]
    cc1 = network.get_cchannels()[1]
    qc0 = network.get_qchannels()[0]
    qc1 = network.get_qchannels()[1]
    qc0.polarization_fidelity = 0.97
    qc1.polarization_fidelity = 0.97

    # instantiate our written keysize protocol
    km1 = KeyManager(tl, keysize, NUM_KEYS)
    km1.lower_protocols.append(n1.protocol_stack[0])
    n1.protocol_stack[0].upper_protocols.append(km1)
    km2 = KeyManager(tl, keysize, NUM_KEYS)
    km2.lower_protocols.append(n2.protocol_stack[0])
    n2.protocol_stack[0].upper_protocols.append(km2)

    # start simulation and record timing
    tl.init()
    km1.send_request()
    tick = time.time()
    tl.run()
    print("execution time %.2f sec" % (time.time() - tick))

    # display our collected metrics
    plt.plot(km1.times, range(1, len(km1.keys) + 1), marker="o")
    plt.xlabel("Simulation time (ms)")
    plt.ylabel("Number of Completed Keys")
    plt.show()

    print("key error rates:")
    for i, e in enumerate(n1.protocol_stack[0].error_rates):
        print("\tkey {}:\t{}%".format(i + 1, e * 100))

    if PRINT_KEYS:
        print("Node 1 keys:")
        for i, key in enumerate(km1.keys):
            print("\t{0:0128b}".format(key))

        print("Node 2 keys:")
        for i, key in enumerate(km2.keys):
            print("\t{0:0128b}".format(key))

# qkd simulator setup and run
KEY_SIZE = 128
DO_GEN = False
filepath = 'src/rnd1.json'
parsedpath = 'src/rnd1parsed.json'
if DO_GEN:
    genNetwork(filepath)
    netparse(filepath, parsedpath)
network = readConfig(parsedpath)
runQKD(network, KEY_SIZE)
