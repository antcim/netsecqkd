import sys
import os
import getopt
import re
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
from keys_exception import NoMoreKeysException

def genNetwork(filepath, nodes_number):
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


def genTopology(network, tl, fidelity):
    sim_nodes = {}

    # Construct dictionary of super qkd nodes
    for node in network.get_nodes_by_type(QKDTopo.QKD_NODE):
        sim_nodes[node.name] = SuperQKDNode(node.name)

    # Make network topology
    for _, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
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
            qchannel = QuantumChannel(
                qchannel_name, tl, 0.0001, 1000, fidelity)
            qchannel.set_ends(sender, dest_receiver)

            # Receiver channels
            cchannel_name = "cchannel[" + source + " to " + dest + ".receiver]"
            cchannel = ClassicalChannel(cchannel_name, tl, 1000, 1)
            cchannel.set_ends(receiver, dest_sender)

            qchannel_name = "qchannel[" + source + " to " + dest + ".receiver]"
            qchannel = QuantumChannel(
                qchannel_name, tl, 0.0001, 1000, fidelity)
            qchannel.set_ends(receiver, dest_sender)

            senderp = MessagingProtocol(
                sender, "msgp", "msgp", dest_receiver, sim_nodes[node.name])
            receiverp = MessagingProtocol(
                receiver, "msgp", "msgp", dest_sender, sim_nodes[node.name])

            sim_nodes[node.name].srqkdnodes[dest] = SRQKDNode(sender, receiver, senderp, receiverp)

    return sim_nodes


def runSim(tl, network, sim_nodes, num_keys, key_size, msg_to_send, print_routing, delta):

    tick = time.time()
    print(f"{Fore.LIGHTMAGENTA_EX}[PAIRED NODES]{Fore.RESET}")
    
    for node in network.get_nodes_by_type(QKDTopo.QKD_NODE):
        neighbors = node.qchannels.keys()
        for k in neighbors:
            A = sim_nodes[node.name].srqkdnodes[k].sender
            B = sim_nodes[k].srqkdnodes[node.name].receiver

            A.set_seed(0)
            B.set_seed(1)

            pair_bb84_protocols(A.protocol_stack[0], B.protocol_stack[0])
            pair_cascade_protocols(A.protocol_stack[1], B.protocol_stack[1])
            print(
                f"{Fore.GREEN}[PAIR]: {Fore.RESET}"
                f"{Fore.LIGHTCYAN_EX}[{A.name}]{Fore.RESET}"
                f" - {Fore.LIGHTBLUE_EX}[{B.name}]{Fore.RESET}")

    # this might be unnecessary with the cascade protocol
    for super_node in sim_nodes.values():
        for srnode in super_node.srqkdnodes.values():
            km1 = KeyManager(tl, key_size, num_keys)
            km1.lower_protocols.append(srnode.sender.protocol_stack[1])
            srnode.sender.protocol_stack[1].upper_protocols.append(km1)

            km2 = KeyManager(tl, key_size, num_keys)
            km2.lower_protocols.append(srnode.receiver.protocol_stack[1])
            srnode.receiver.protocol_stack[1].upper_protocols.append(km2)

            srnode.addKeyManagers(km1, km2)

    # Start simulation and record timing
    # Generate routing tables
    topo_manager = NewQKDTopo(sim_nodes)

    # pick a destination node for each node in the network
    sender_receiver = {}

    for i in range(0, msg_to_send + 1):
        sender_node = random.randint(0, len(list(sim_nodes))-1)
        receiver_node = random.randint(0, len(list(sim_nodes))-1)

        while sender_node == receiver_node:
            receiver_node = random.randint(0, len(list(sim_nodes))-1)

        sender_receiver[f"node{sender_node}"] = f"node{receiver_node}"

    print(f"{Fore.YELLOW}[sender_receiver]:{Fore.RESET} {sender_receiver}")

    # Generate the message with the destination
    plaintext = key_size * '1'
    
    successes = 0
    losses = 0

    # execute qkd for every node in the network
    tl.init()
    for super_node in sim_nodes.values():
        for sr_node in super_node.srqkdnodes.values():
            print(f"{Fore.LIGHTCYAN_EX}[SEND QKD REQUEST]{Fore.RESET} {sr_node.sender.name}")
            sr_node.senderkm.send_request()
    tl.run()        

    # generate the routing tables
    topo_manager.gen_forward_tables()

    # schedule messages
    for sender, receiver in sender_receiver.items():
        try:
            message = {"dest": receiver, "payload": plaintext}
            message = json.dumps(message)
            tl.init()
            print(f"{Fore.LIGHTCYAN_EX}[Message]:{Fore.RESET} {sender} to {receiver}")
            sim_nodes[sender].sendMessage(tl, receiver, message, delta)
            tl.run()
        except NoMoreKeysException:
            losses += 1
        else:
            successes +=1

    print(
        f"{Fore.YELLOW}[Successful Messages]{Fore.RESET}{successes}")
    print(
        f"{Fore.YELLOW}[Dropped Messages]{Fore.RESET}{losses}")
    print(
        f"{Fore.YELLOW}[Message Time (Simulation)]{Fore.RESET}{tl.now()} ps")

    for super_node in sim_nodes.values():
        for sr_node in super_node.srqkdnodes.values():
            sr_node.senderMetrics()

    print(
        f"{Fore.YELLOW}[Execution Time]{Fore.RESET}{(time.time() - tick):0.4f} s")

def main(argv):

    current_sim = "simulations/sim_" + \
        str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "/"
    num_keys = 3
    key_size = 128
    do_gen = True
    print_routing = False
    filename = 'graph_networkx.json'
    parsename = 'graph_sequence.json'
    fidelity = 0.97
    nodes_number = 10
    msg_to_send = 3
    output_html = False
    delta = 1 #1 second

    opts, _ = getopt.getopt(argv, "f:n:s:ekvq:rd:m:ht:")
    for opt, arg in opts:
        # network graph filepath
        if opt in ['-f']:
            do_gen = False
            filename = arg
        # number of keys to generate
        elif opt in ['-n']:
            num_keys = int(arg)
        # keys bits to generate
        elif opt in ['-s']:
            key_size = int(arg)
        # fidelity of quantum channels
        elif opt in ['-q']:
            fidelity = float(arg)
        # print routing tables
        elif opt in ['-r']:
            print_routing = True
        # number of nodes to generate
        elif opt in ['-d']:
            nodes_number = int(arg)
        # number of messages to send
        elif opt in ['-m']:
            msg_to_send = int(arg)
        # generate html output
        elif opt in ['-h']:
            output_html = True
        # set delta
        elif opt in ['-t']:
            delta = float(arg)

    delta = delta * (10**12)

    os.makedirs(os.path.dirname(current_sim), exist_ok=True)
    sys.stdout = Logger(current_sim + "sim_output.txt")

    print(f"{Fore.YELLOW}[Simulation Command]:{Fore.RESET} python3 {' '.join(sys.argv[0:])}")

    if do_gen:
        graph = genNetwork(current_sim + filename, nodes_number)
        while len(graph.nodes()) < 2:
            graph = genNetwork(current_sim + filename, nodes_number)
    else:
        print(
            f"{Fore.LIGHTCYAN_EX}[Loaded Network Graph From File: {filename}]{Fore.CYAN}")
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
    sim_nodes = genTopology(network, tl, fidelity)
    runSim(tl, network, sim_nodes, num_keys, key_size, msg_to_send, print_routing, delta)

    sys.stdout.flush()
    if output_html:
        os.system("cat " + current_sim + "sim_output.txt"
              + " | aha --black > " + current_sim + "sim_output.html")


if __name__ == "__main__":
    main(sys.argv[1:])
