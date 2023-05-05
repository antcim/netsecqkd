import copy
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
from superqkdnode import SuperQKDNode
from srqkdnode import SRQKDNode


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

    sim_nodes = {}

    # construct dictionary of super qkd nodes
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        print("Links for {}".format(node.name))
        sim_nodes[node.name] = SuperQKDNode(node.name)
    
    # make connections
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        for key in node.cchannels.keys():
            sender = node
            receiver = copy.deepcopy(node)
            sim_nodes[node.name].addSRQKDNode(SRQKDNode(sender, receiver))
            print("Channel: " + str(node.cchannels[key].name))
            print("Sender: " + str(node.cchannels[key].sender.name))
            print("Receiver: " + str(node.cchannels[key].receiver))

    for key, node in sim_nodes.items():
        print(key, ' : ', node.name)
        for srqknode in node.srqkdnodes:
            print(key, 'sender : ', srqknode.sender.name)
            print(key, 'receiver : ', srqknode.receiver.name)

    # QKD from 0 to 1
    n0 = sim_nodes["node0"].srqkdnodes[0].sender
    n1 = sim_nodes["node1"].srqkdnodes[0].receiver

    print(n0.name)
    print(n1.name)
    print(tl.stop_time)

    n0.set_seed(0)
    n1.set_seed(1)
    pair_bb84_protocols(n0.protocol_stack[0], n1.protocol_stack[0])

    for key, channel in n0.cchannels.items():
        print(key + " "+ channel.name)

    # index of dict is the endpoint of the channel
    cc0 = n0.cchannels["node1"]
    cc1 = n1.cchannels["node0"]
    qc0 = n0.qchannels["node1"]
    qc1 = n1.qchannels["node0"]
    qc0.polarization_fidelity = 0.97
    qc1.polarization_fidelity = 0.97

    # instantiate our written keysize protocol
    km1 = KeyManager(tl, keysize, NUM_KEYS)
    km1.lower_protocols.append(n0.protocol_stack[0])
    n0.protocol_stack[0].upper_protocols.append(km1)
    km2 = KeyManager(tl, keysize, NUM_KEYS)
    km2.lower_protocols.append(n1.protocol_stack[0])
    n1.protocol_stack[0].upper_protocols.append(km2)

    # QKD from 1 to 0
    n2 = sim_nodes["node1"].srqkdnodes[0].sender
    n3 = sim_nodes["node0"].srqkdnodes[0].receiver

    print(n2.name)
    print(n3.name)
    print(tl.stop_time)

    n2.set_seed(0)
    n3.set_seed(1)
    pair_bb84_protocols(n2.protocol_stack[0], n3.protocol_stack[0])

    for key, channel in n2.cchannels.items():
        print(key + " "+ channel.name)

    # index of dict is the endpoint of the channel
    cc0 = n2.cchannels["node0"]
    cc1 = n3.cchannels["node1"]
    qc0 = n2.qchannels["node0"]
    qc1 = n3.qchannels["node1"]
    qc0.polarization_fidelity = 0.97
    qc1.polarization_fidelity = 0.97

    # instantiate our written keysize protocol
    km3 = KeyManager(tl, keysize, NUM_KEYS)
    km3.lower_protocols.append(n2.protocol_stack[0])
    n2.protocol_stack[0].upper_protocols.append(km3)
    km4 = KeyManager(tl, keysize, NUM_KEYS)
    km4.lower_protocols.append(n3.protocol_stack[0])
    n3.protocol_stack[0].upper_protocols.append(km4)

    # start simulation and record timing
    tl.init()
    km1.send_request()
    km3.send_request()
    tick = time.time()
    tl.run()
    print("execution time %.2f sec" % (time.time() - tick))

    # display our collected metrics
    plt.plot(km1.times, range(1, len(km1.keys) + 1), marker="o")
    plt.xlabel("Simulation time (ms)")
    plt.ylabel("Number of Completed Keys")
    plt.show()

    # display our collected metrics
    plt.plot(km3.times, range(1, len(km3.keys) + 1), marker="o")
    plt.xlabel("Simulation time (ms)")
    plt.ylabel("Number of Completed Keys")
    plt.show()

    print("key error rates:")
    for i, e in enumerate(n0.protocol_stack[0].error_rates):
        print("\tkey {}:\t{}%".format(i + 1, e * 100))

    print("key error rates:")
    for i, e in enumerate(n3.protocol_stack[0].error_rates):
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
parsedpath = 'src/twonodes.json'
if DO_GEN:
    genNetwork(filepath)
    netparse(filepath, parsedpath)
network = readConfig(parsedpath)
runQKD(network, KEY_SIZE)
