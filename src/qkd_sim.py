import copy
from xml.dom import Node
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

################# KEY MANAGER #########################

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

######################################################

def genNetwork(filepath):
    # generate random graph
    G = nx.random_lobster(10, 0.2, 0.25)
    # JSON representation
    jsonG = nx.node_link_data(G)
    with open(filepath, 'w') as f:
        json.dump(jsonG, f, ensure_ascii=False)


def readConfig(filepath):
    return QKDTopo(filepath)


def genTopology(network, tl):
    sim_nodes = {}

    # construct dictionary of super qkd nodes
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        sim_nodes[node.name] = SuperQKDNode(node.name)
    
    # make connections
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        for key in node.cchannels.keys():

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
            qchannel = QuantumChannel(qchannelName, tl, 0.0001, 1000)
            qchannel.set_ends(sender, destReceiver)

            # receiver channels
            cchannelName = "cchannel[" + source + " to " +  dest + ".receiver]" 
            cchannel = ClassicalChannel(cchannelName, tl, 1000, 1)
            cchannel.set_ends(receiver, destSender)

            qchannelName = "qchannel[" + source + " to " +  dest + ".receiver]" 
            qchannel = QuantumChannel(qchannelName, tl, 0.0001, 1000)
            qchannel.set_ends(receiver, destSender)

            sim_nodes[node.name].addSRQKDNode(SRQKDNode(sender, receiver))

    for key, node in sim_nodes.items():
        print(key, 'SRQKDNode of ', node.name)
        for srqknode in node.srqkdnodes:
            print(key, 'sender : ', srqknode.sender.name)
            print(key, 'receiver : ', srqknode.receiver.name)
        print("\n")

    return sim_nodes

def runSim(tl, network, sim_nodes, keysize):
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        neighbors = node.qchannels.keys()
        for k in neighbors:
            s_name = node.name + " to " + k +".sender"
            d_name = k + " to " + node.name + ".receiver"

            A = None
            B = None

            # find right sender in node
            for n in sim_nodes[node.name].srqkdnodes:
                if n.sender.name == s_name:
                    A = n.sender

            # find right receiver in neighbor
            for n in sim_nodes[k].srqkdnodes:
                if n.receiver.name == d_name:
                    B = n.receiver

            A.set_seed(0)
            B.set_seed(1)

            pair_bb84_protocols(A.protocol_stack[0], B.protocol_stack[0])
            print("[PAIR]", A.name, "and", B.name)
    
    key_managers = {}

    for n in sim_nodes.values():
        for srnode in n.srqkdnodes:
            km1 = KeyManager(tl, keysize, NUM_KEYS)
            km1.lower_protocols.append(srnode.sender.protocol_stack[0])
            srnode.sender.protocol_stack[0].upper_protocols.append(km1)

            km2 = KeyManager(tl, keysize, NUM_KEYS)
            km2.lower_protocols.append(srnode.receiver.protocol_stack[0])
            srnode.receiver.protocol_stack[0].upper_protocols.append(km2)

            key_managers[srnode.sender.name] = km1
            key_managers[srnode.receiver.name] = km2
    

    # start simulation and record timing
    tl.init()
    
    senders = list(filter(lambda KM: KM.endswith('.sender'), key_managers))

    for km in senders:
        key_managers[km].send_request()
    
    tick = time.time()
    tl.run()
    print("execution time %.2f sec" % (time.time() - tick))

    # print error rate for each sender
    if PRINT_ERROR_RATE:
        for sn in sim_nodes.values():
            for n in sn.srqkdnodes:
                A = n.sender
                print("[",A.name,"] key error rates:")
                for i, e in enumerate(A.protocol_stack[0].error_rates):
                    print("\tkey {}:\t{}%".format(i + 1, e * 100))

    if PRINT_KEYS:
        # print keys for each sender
        for s in senders:
            print("[",s,"] keys:")
            for i, key in enumerate(key_managers[s].keys):
                print("\t{0:0128b}".format(key))


# qkd simulator setup and run
NUM_KEYS = 25
KEY_SIZE = 128
DO_GEN = True
PRINT_KEYS = False
PRINT_ERROR_RATE = False
filepath = 'src/rnd.json'
parsedpath = 'src/rndp.json'
if DO_GEN:
    genNetwork(filepath)
    netparse(filepath, parsedpath)
network = readConfig(parsedpath)
tl = Timeline(5000 * 1e9)
sim_nodes = genTopology(network, tl)
runSim(tl, network, sim_nodes, KEY_SIZE)

