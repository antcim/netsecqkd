import sys
import getopt
import time
import matplotlib.pyplot as plt

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


# defalut simulation values
num_keys = 3
key_size = 128
do_gen = True
print_keys = False
print_error = False
filepath = 'src/rnd.json'
parsepath = 'src/rndp.json'
verbose = False
fidelity = 1
draw = False


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
    # G = nx.star_graph(10)
    # G = nx.ladder_graph(10)
    # G = nx.path_graph(10)
    # G = nx.cycle_graph(10)
    # JSON representation
    jsonG = nx.node_link_data(G)
    with open(filepath, 'w') as f:
        json.dump(jsonG, f, ensure_ascii=False)

    if draw:
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_size = 500)
        nx.draw_networkx_labels(G, pos)
        nx.draw_networkx_edges(G, pos, edge_color='r', arrows=True)
        nx.draw_networkx_edges(G, pos, arrows=False)
        plt.show()


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
            cchannelName = "cchannel[" + source + " to " + dest + ".sender]"
            cchannel = ClassicalChannel(cchannelName, tl, 1000, 1)
            cchannel.set_ends(sender, destReceiver)

            qchannelName = "qchannel[" + source + " to " + dest + ".sender]"
            qchannel = QuantumChannel(qchannelName, tl, 0.0001, 1000, fidelity)
            qchannel.set_ends(sender, destReceiver)

            # receiver channels
            cchannelName = "cchannel[" + source + " to " + dest + ".receiver]"
            cchannel = ClassicalChannel(cchannelName, tl, 1000, 1)
            cchannel.set_ends(receiver, destSender)

            qchannelName = "qchannel[" + source + " to " + dest + ".receiver]"
            qchannel = QuantumChannel(qchannelName, tl, 0.0001, 1000, fidelity)
            qchannel.set_ends(receiver, destSender)

            sim_nodes[node.name].addSRQKDNode(SRQKDNode(sender, receiver))

    if verbose:
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
            s_name = node.name + " to " + k + ".sender"
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
            km1 = KeyManager(tl, keysize, num_keys)
            km1.lower_protocols.append(srnode.sender.protocol_stack[0])
            srnode.sender.protocol_stack[0].upper_protocols.append(km1)

            km2 = KeyManager(tl, keysize, num_keys)
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
    if print_error:
        for sn in sim_nodes.values():
            for n in sn.srqkdnodes:
                A = n.sender
                print("[", A.name, "] key error rates:")
                for i, e in enumerate(A.protocol_stack[0].error_rates):
                    print("\tkey {}:\t{}%".format(i + 1, e * 100))

    if print_keys:
        # print keys for each sender
        for s in senders:
            print("[", s, "] keys:")
            for i, key in enumerate(key_managers[s].keys):
                print("\t{0:0128b}".format(key))


def main(argv):

    global num_keys
    global key_size
    global do_gen
    global print_keys
    global print_error
    global filepath
    global parsepath
    global verbose
    global fidelity
    global draw


    opts, args = getopt.getopt(argv, "f:n:s:ekvq:d")
    for opt, arg in opts:
        if opt == '-f':
            do_gen = False
            parsepath = arg
        elif opt in ['-n']:
            num_keys = int(arg)
        elif opt in ['-s']:
            key_size = int(arg)
        elif opt in ['-e']:
            print_error = True
        elif opt in ['-k']:
            print_keys = True
        elif opt in ['-v']:
            verbose = True
        elif opt in ['-q']:
            print_error = True
            fidelity = float(arg)
        elif opt in ['-d']:
            draw = True

    if do_gen:
        genNetwork(filepath)
        netparse(filepath, parsepath)
    network = readConfig(parsepath)
    tl = Timeline(5000 * 1e9)
    sim_nodes = genTopology(network, tl)
    runSim(tl, network, sim_nodes, key_size)


if __name__ == "__main__":
    main(sys.argv[1:])
