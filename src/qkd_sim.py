import sys
import os
import getopt
import time
from datetime import datetime
import matplotlib.pyplot as plt
import networkx as nx
import json
from colorama import Fore
import random

# sequence lib
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.topology.qkd_topo import QKDTopo

# netsecqkd lib
from netparser import netparse
from superqkdnode import SuperQKDNode
from srqkdnode import SRQKDNode
from newqkdtopo import NewQKDTopo
from messaging import MessagingProtocol
from keymanager import KeyManager

# defalut simulation values
current_sim = "sim/sim_" + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) +"/"
num_keys = 3
key_size = 128
do_gen = True
print_keys = False
print_error = False
print_routing = False
filename = 'graph_networkx.json'
parsename = 'graph_sequence.json'
verbose = False
fidelity = 1

def genNetwork(filepath):
    G = nx.random_internet_as_graph(50)
    jsonG = nx.node_link_data(G)
    with open(filepath, 'w') as f:
        json.dump(jsonG, f, ensure_ascii=False)
    return G


def drawToFile(graph, filepath):
    pos = nx.kamada_kawai_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=50, margins=0.01)
    nx.draw_networkx_labels(graph, pos, font_size = 5, font_color='w')
    nx.draw_networkx_edges(graph, pos, width=0.5)
    plt.savefig(filepath, dpi=500, orientation='landscape', bbox_inches='tight')


def readConfig(filepath):
    return QKDTopo(filepath)


def genTopology(network, tl):
    sim_nodes = {}

    # construct dictionary of super qkd nodes
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        sim_nodes[node.name] = SuperQKDNode(node.name)

    # make network topology
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

            senderp = MessagingProtocol(
                sender, "msgp", "msgp", destReceiver, sim_nodes[node.name])
            receiverp = MessagingProtocol(
                receiver, "msgp", "msgp", destSender, sim_nodes[node.name])

            sim_nodes[node.name].addSRQKDNode(
                SRQKDNode(sender, receiver, senderp, receiverp))

    if verbose:
        for key, node in sim_nodes.items():
            print(key, 'SRQKDNode of ', node.name)
            for srqknode in node.srqkdnodes:
                print(key, 'sender : ', srqknode.sender.name)
                print(key, 'receiver : ', srqknode.receiver.name)
            print("\n")

    return sim_nodes


def runSim(tl, network, sim_nodes, keysize):
    print(Fore.LIGHTMAGENTA_EX, "-----------------", Fore.RESET)
    print(Fore.LIGHTMAGENTA_EX, "| PAIRING NODES |", Fore.RESET)
    print(Fore.LIGHTMAGENTA_EX, "-----------------", Fore.RESET)

    tick = time.time()
    pairTick = time.time()

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
            print(Fore.GREEN, "[PAIR]", Fore.RESET, Fore.LIGHTCYAN_EX, "[",
                  A.name, "]", Fore.RESET, Fore.LIGHTBLUE_EX, "[", B.name, "]",Fore.RESET)

    print(Fore.YELLOW, "[Pairing Time]", Fore.RESET, "%.4f sec" % (time.time() - pairTick))

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

            srnode.addKeyManagers(km1, km2)

    # generate routing tables
    NewQKDTopo(current_sim + parsename, sim_nodes)

    if print_routing:
        for n in sim_nodes:
            print(Fore.LIGHTMAGENTA_EX , "\nROUTING TABLE ", n, Fore.RESET)
            for i, k in sim_nodes[n].routing_table.items():
                print("TO ", Fore.LIGHTBLUE_EX , i, Fore.RESET, "Path: ", Fore.LIGHTCYAN_EX , k, Fore.RESET)

    # start simulation and record timing
    tl.init()

    # send QKD requests
    senders = list(filter(lambda KM: KM.endswith('.sender'), key_managers))
    qkdTick = time.time()
    for km in senders:
        key_managers[km].send_request()

    tl.show_progress = False
    tl.run()

    # this is to avoid clashes on classical channels when multiple messages are sent
    while tl.schedule_counter > tl.run_counter:
        continue

    print(Fore.YELLOW, "[QKD Time]", Fore.RESET, "%.4f sec" % (time.time() - qkdTick))

    tl.init()
    # send messages encrypted with QKD keys on classical channels
    plaintext = "11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
    

    print(Fore.LIGHTMAGENTA_EX, "-----------------", Fore.RESET)
    print(Fore.LIGHTMAGENTA_EX, "| SENT MESSAGES |", Fore.RESET)
    print(Fore.LIGHTMAGENTA_EX, "-----------------", Fore.RESET)

    random_sender_node_num = random.randint(0,len(list(sim_nodes))-1)
    random_sender_node = list(sim_nodes.keys())[random_sender_node_num]

    random_receiver_node_num = random.randint(0,len(list(sim_nodes))-1)
    while random_sender_node_num == random_receiver_node_num:
        random_receiver_node_num = random.randint(0,len(list(sim_nodes))-1)
    random_receiver_node = list(sim_nodes.keys())[random_receiver_node_num]   

    print(Fore.YELLOW, "[Message from ", random_sender_node, " to ",random_receiver_node , "]", Fore.RESET)

    message = {"dest":random_receiver_node, "payload":plaintext}
    message = json.dumps(message)

    messageTick = time.time()
    sim_nodes[random_sender_node].sendMessage(tl, random_receiver_node, message)

    tl.run()

    print(Fore.YELLOW, "[Message Time]", Fore.RESET, "%.4f sec" % (time.time() - messageTick))
    print(Fore.YELLOW, "[Execution Time]", Fore.RESET, "%.4f sec" % (time.time() - tick))

    # print error rate for each sender
    if print_error:
        for sn in sim_nodes.values():
            for n in sn.srqkdnodes:
                A = n.sender
                print("[", A.name, "] key error rates:")
                for i, e in enumerate(A.protocol_stack[0].error_rates):
                    print("\tkey {}:\t{}%".format(i + 1, e * 100))

    if print_keys:
        key_format = "{0:0"+str(key_size)+"b}"
        # print keys for each sender
        for s in senders:
            print("[", s, "] keys:")
            for i, key in enumerate(key_managers[s].keys):
                print(key_format.format(key))


def main(argv):
    global current_sim
    global num_keys
    global key_size
    global do_gen
    global print_keys
    global print_error
    global filename
    global parsename
    global verbose
    global fidelity
    global print_routing

    opts, args = getopt.getopt(argv, "f:n:s:ekvq:r")
    for opt, arg in opts:
        if opt == '-f':
            do_gen = False
            filename = arg
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
        elif opt in ['-r']:
            print_routing = True

    os.makedirs(os.path.dirname(current_sim), exist_ok=True)
    sys.stdout = open(current_sim + "sim_output.txt", 'w')

    if do_gen:
        graph = genNetwork(current_sim + filename)
        while len(graph.nodes()) < 2: 
            graph = genNetwork(current_sim + filename)
    else:
        print("FILENAME: " , filename)
        with open(filename, 'r') as f:
            js_graph = json.load(f)
        graph = nx.readwrite.json_graph.node_link_graph(js_graph)
        filename = 'graph_networkx.json'
        with open(current_sim + filename, 'w') as f:
            json.dump(js_graph, f, ensure_ascii=False)

    drawToFile(graph, current_sim + "network_graph.png")
    netparse(current_sim + filename, current_sim + parsename)
    network = readConfig(current_sim + parsename)
    
    tl = Timeline()
    sim_nodes = genTopology(network, tl)
    runSim(tl, network, sim_nodes, key_size)

    sys.stdout.flush()
    os.system("cat " + current_sim + "sim_output.txt" + " | aha --black > " + current_sim + "sim_output.html")
    os.system("cat " + current_sim + "sim_output.txt")

if __name__ == "__main__":
    main(sys.argv[1:])
