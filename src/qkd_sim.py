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

# Sequence lib
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.qkd.cascade import pair_cascade_protocols
from sequence.topology.qkd_topo import QKDTopo

# Netsecqkd lib
from netparser import netparse
from superqkdnode import SuperQKDNode
from srqkdnode import SRQKDNode
from newqkdtopo import NewQKDTopo
from messaging import MessagingProtocol
from keymanager import KeyManager
from logger import Logger

# Defalut simulation values
current_sim = "sim/sim_" + str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "/"
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
nodes_number = 50


def genNetwork(filepath):
    G = nx.random_internet_as_graph(nodes_number)
    json_G = nx.node_link_data(G)
    with open(filepath, 'w') as f:
        json.dump(json_G, f, ensure_ascii=False)
    return G


def drawToFile(graph, filepath):
    pos = nx.kamada_kawai_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=50, margins=0.01)
    nx.draw_networkx_labels(graph, pos, font_size=5, font_color='w')
    nx.draw_networkx_edges(graph, pos, width=0.5)
    plt.savefig(filepath, dpi=500, orientation='landscape',
                bbox_inches='tight')


def readConfig(filepath):
    return QKDTopo(filepath)


def genTopology(network, tl):
    sim_nodes = {}

    # Construct dictionary of super qkd nodes
    for node in network.get_nodes_by_type(QKDTopo.QKD_NODE):
        sim_nodes[node.name] = SuperQKDNode(node.name)

    # Make network topology
    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        for key in node.cchannels.keys():

            source = node.name
            dest = node.cchannels[key].receiver

            sender_name = source + " to " + dest + ".sender"
            sender = QKDNode(sender_name, tl)

            receiver_name = source + " to " + dest + ".receiver"
            receiver = QKDNode(receiver_name, tl)

            dest_receiver = dest + " to " + source + ".receiver"
            dest_sender = dest + " to " + source + ".sender"

            # Sender channels
            cchannel_name = "cchannel[" + source + " to " + dest + ".sender]"
            cchannel = ClassicalChannel(cchannel_name, tl, 1000, 1)
            cchannel.set_ends(sender, dest_receiver)

            qchannel_name = "qchannel[" + source + " to " + dest + ".sender]"
            qchannel = QuantumChannel(qchannel_name, tl, 0.0001, 1000, fidelity)
            qchannel.set_ends(sender, dest_receiver)

            # Receiver channels
            cchannel_name = "cchannel[" + source + " to " + dest + ".receiver]"
            cchannel = ClassicalChannel(cchannel_name, tl, 1000, 1)
            cchannel.set_ends(receiver, dest_sender)

            qchannel_name = "qchannel[" + source + " to " + dest + ".receiver]"
            qchannel = QuantumChannel(qchannel_name, tl, 0.0001, 1000, fidelity)
            qchannel.set_ends(receiver, dest_sender)

            senderp = MessagingProtocol(
                sender, "msgp", "msgp", dest_receiver, sim_nodes[node.name])
            receiverp = MessagingProtocol(
                receiver, "msgp", "msgp", dest_sender, sim_nodes[node.name])

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
    pair_tick = time.time()

    for i, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        neighbors = node.qchannels.keys()
        for k in neighbors:
            s_name = node.name + " to " + k + ".sender"
            d_name = k + " to " + node.name + ".receiver"

            A = None
            B = None

            # Find right sender in node
            for n in sim_nodes[node.name].srqkdnodes:
                if n.sender.name == s_name:
                    A = n.sender

            # Find right receiver in neighbor
            for n in sim_nodes[k].srqkdnodes:
                if n.receiver.name == d_name:
                    B = n.receiver

            A.set_seed(0)
            B.set_seed(1)

            pair_bb84_protocols(A.protocol_stack[0], B.protocol_stack[0])
            # pair_cascade_protocols(A.protocol_stack[1], B.protocol_stack[1])
            print(
                f"{Fore.GREEN}[PAIR]{Fore.RESET}" 
                f"{Fore.LIGHTCYAN_EX}[{A.name}]{Fore.RESET}"
                f"{Fore.LIGHTBLUE_EX}[{B.name}]{Fore.RESET}")

    print(
        f"{Fore.YELLOW}[Pairing Time]{Fore.RESET}{(time.time() - pair_tick):0.4f} s")

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

    # Start simulation and record timing
    tl.init()

    # Send QKD requests
    senders = list(filter(lambda KM: KM.endswith('.sender'), key_managers))
    qkd_tick = time.time()
    for km in senders:
        key_managers[km].send_request()

    tl.show_progress = False
    tl.run()

    # Generate routing tables
    topo_manager = NewQKDTopo(sim_nodes)

    if print_routing:
        for n in sim_nodes:
            print(Fore.LIGHTMAGENTA_EX, "\nROUTING TABLE ", n, Fore.RESET)
            for i, k in sim_nodes[n].routing_table.items():
                print("TO ", Fore.LIGHTBLUE_EX, i, Fore.RESET,
                      "Path: ", Fore.LIGHTCYAN_EX, k, Fore.RESET)

    for n in sim_nodes['node2'].srqkdnodes:
        if n.sender.name == "node2 to node4.sender":
            n.senderkm.keys = []


    # This is to avoid clashes on classical channels when
    # multiple messages are sent
    print(f"SCHEDULED EVENT {tl.schedule_counter}")

    # while tl.schedule_counter > tl.run_counter:
    #     continue

    print(f"{Fore.YELLOW}[QKD Time]{Fore.RESET}{(time.time() - qkd_tick):0.4f} s")

    tl.init()
    # Send messages encrypted with QKD keys on classical channels
    plaintext = keysize * '1'

    print(Fore.LIGHTMAGENTA_EX, "-----------------", Fore.RESET)
    print(Fore.LIGHTMAGENTA_EX, "| SENT MESSAGES |", Fore.RESET)
    print(Fore.LIGHTMAGENTA_EX, "-----------------", Fore.RESET)

    # random_sender_node_num = random.randint(0, len(list(sim_nodes))-1)
    # random_sender_node = list(sim_nodes.keys())[random_sender_node_num]

    # random_receiver_node_num = random.randint(0, len(list(sim_nodes))-1)
    # while random_sender_node_num == random_receiver_node_num:
    #     random_receiver_node_num = random.randint(0, len(list(sim_nodes))-1)
    # random_receiver_node = list(sim_nodes.keys())[random_receiver_node_num]

    # print(Fore.YELLOW, "[Message from ", random_sender_node, " to ",
    #       random_receiver_node, "]", Fore.RESET)

    # message = {"dest": random_receiver_node, "payload": plaintext}
    # message = json.dumps(message)

    message_tick = time.time()

    # manually pick nodes to send messages
    message = {"dest": 'node7', "payload": plaintext}
    message = json.dumps(message)
    result = sim_nodes['node9'].sendMessage(
        tl, 'node7', message)

    tl.run()

    tl.init()
    
    if not result:
        topo_manager.gen_forward_tables()
        sim_nodes['node9'].sendMessage(tl, 'node7', message)
    
    tl.run()

    print(
        f"{Fore.YELLOW}[Message Time]{Fore.RESET}{(time.time() - message_tick):0.4f} s")
    print(
        f"{Fore.YELLOW}[Execution Time]{Fore.RESET}{(time.time() - tick):0.4f} s")

    # Print error rate for each sender
    if print_error:
        for sn in sim_nodes.values():
            for n in sn.srqkdnodes:
                A = n.sender
                print("[", A.name, "] key error rates:")
                for i, e in enumerate(A.protocol_stack[0].error_rates):
                    print(f"\tkey {i + 1}:\t{e * 100}%")

    if print_keys:
        key_format = "{0:0"+str(key_size)+"b}"
        # Print keys for each sender
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
    global nodes_number

    opts, args = getopt.getopt(argv, "f:n:s:ekvq:rd:")
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
        elif opt in ['-d']:
            nodes_number = int(arg)

    os.makedirs(os.path.dirname(current_sim), exist_ok=True)
    sys.stdout = Logger(current_sim + "sim_output.txt")

    if do_gen:
        graph = genNetwork(current_sim + filename)
        while len(graph.nodes()) < 2:
            graph = genNetwork(current_sim + filename)
    else:
        print(f"{Fore.LIGHTCYAN_EX}[Loaded Network Graph From File: {filename}]{Fore.CYAN}")
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
    os.system("cat " + current_sim + "sim_output.txt"
              + " | aha --black > " + current_sim + "sim_output.html")


if __name__ == "__main__":
    main(sys.argv[1:])
