import sys
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

    # tl = network.get_timeline() reading it from json doesn't work
    tl = Timeline(5000 * 1e9)

    sim_nodes = {}

    # construct dictionary of super qkd nodes
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        sim_nodes[node.name] = SuperQKDNode(node.name + "TEST")
    
    # make connections
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        print("Links for {}".format(node.name))
        for key in node.cchannels.keys():
            print("Channel: " + str(node.cchannels[key].name))
            print("Sender: " + str(node.cchannels[key].sender.name))
            print("Receiver: " + str(node.cchannels[key].receiver))

            source = node.name
            dest = node.cchannels[key].receiver

            senderName = source + " to " + dest + ".sender" 
            sender = QKDNode(senderName, tl, stack_size=1)

            receiverName = source + " to " + dest + ".receiver" 
            receiver = QKDNode(receiverName, tl, stack_size=1)

            destReceiver = dest + " to " + source + ".receiver" 
            destSender = dest + " to " + source + ".sender"

            # sender channels
            cchannelName = "cchannel[" + source + " to " +  dest + ".sender]" 
            cchannel = ClassicalChannel(cchannelName, tl, 1000, 1)
            cchannel.set_ends(sender, destReceiver)

            qchannelName = "qchannel[" + source + " to " +  dest + ".sender]" 
            qchannel = QuantumChannel(qchannelName, tl, 0.0001, 1000, 0.97)
            qchannel.set_ends(sender, destReceiver)

            # receiver channels
            cchannelName = "cchannel[" + source + " to " +  dest + ".receiver]" 
            cchannel = ClassicalChannel(cchannelName, tl, 1000, 1)
            cchannel.set_ends(receiver, destSender)

            qchannelName = "qchannel[" + source + " to " +  dest + ".receiver]" 
            qchannel = QuantumChannel(qchannelName, tl, 0.0001, 1000, 0.97)
            qchannel.set_ends(receiver, destSender)

            sim_nodes[node.name].addSRQKDNode(SRQKDNode(sender, receiver))

            

            print(senderName)
            print(receiverName)

        print("\n")

    # for key, node in sim_nodes.items():
    #     print(key, 'SRQKDNode of ', node.name)
    #     for srqknode in node.srqkdnodes:
    #         print(key, 'sender : ', srqknode.sender.name)
    #         print(key, 'receiver : ', srqknode.receiver.name)
    #     print("\n")

    # QKD from 0 to 1
    print("QKD from 0 to 1")

    alice = sim_nodes["node0"].srqkdnodes[0].sender
    bob = sim_nodes["node1"].srqkdnodes[0].receiver

    # print("NAME ALICE: ", alice.name)

    alice.set_seed(0)
    bob.set_seed(1)

    pair_bb84_protocols(alice.protocol_stack[0], bob.protocol_stack[0])

    # print("\nCChannel of : ", alice.name)
    # for key, channel in alice.cchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # print("\nCChannel of : ", bob.name)
    # for key, channel in bob.cchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # print("\nQChannel of : ", alice.name)
    # for key, channel in alice.qchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # print("\nQChannel of : ", bob.name)
    # for key, channel in bob.qchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # index of dict is the endpoint of the channel
    cc0 = alice.cchannels["node1 to node0.receiver"]
    cc1 = bob.cchannels["node0 to node1.sender"]
    qc0 = alice.qchannels["node1 to node0.receiver"]
    qc1 = bob.qchannels["node0 to node1.sender"]
    qc0.polarization_fidelity = 1
    qc1.polarization_fidelity = 1

    # instantiate our written keysize protocol
    km1 = KeyManager(tl, keysize, NUM_KEYS)
    km1.lower_protocols.append(alice.protocol_stack[0])
    alice.protocol_stack[0].upper_protocols.append(km1)
    km2 = KeyManager(tl, keysize, NUM_KEYS)
    km2.lower_protocols.append(bob.protocol_stack[0])
    bob.protocol_stack[0].upper_protocols.append(km2)

    # QKD from 1 to 0
    print("QKD from 1 to 0")

    anna = sim_nodes["node1"].srqkdnodes[0].sender
    berny = sim_nodes["node0"].srqkdnodes[0].receiver

    anna.set_seed(0)
    berny.set_seed(1)

    pair_bb84_protocols(anna.protocol_stack[0], berny.protocol_stack[0])

    # print("\nCChannel of : ", anna.name)
    # for key, channel in anna.cchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # print("\nCChannel of : ", berny.name)
    # for key, channel in berny.cchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # print("\nQChannel of : ", anna.name)
    # for key, channel in anna.qchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # print("\nQChannel of : ", berny.name)
    # for key, channel in berny.qchannels.items():
    #     print("key: ", key , " name: " , channel.name, "\n")

    # index of dict is the endpoint of the channel
    cc0 = anna.cchannels["node0 to node1.receiver"]
    cc1 = berny.cchannels["node1 to node0.sender"]
    qc0 = anna.qchannels["node0 to node1.receiver"]
    qc1 = berny.qchannels["node1 to node0.sender"]
    qc0.polarization_fidelity = 1
    qc1.polarization_fidelity = 1

    # instantiate our written keysize protocol
    km3 = KeyManager(tl, keysize, NUM_KEYS)
    km3.lower_protocols.append(anna.protocol_stack[0])
    anna.protocol_stack[0].upper_protocols.append(km3)
    km4 = KeyManager(tl, keysize, NUM_KEYS)
    km4.lower_protocols.append(berny.protocol_stack[0])
    berny.protocol_stack[0].upper_protocols.append(km4)

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
    for i, e in enumerate(alice.protocol_stack[0].error_rates):
        print("\tkey {}:\t{}%".format(i + 1, e * 100))

    print("key error rates:")
    for i, e in enumerate(anna.protocol_stack[0].error_rates):
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