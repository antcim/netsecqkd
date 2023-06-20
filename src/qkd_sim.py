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

# sequence modules
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.qkd.cascade import pair_cascade_protocols
from sequence.topology.qkd_topo import QKDTopo

# netsecqkd modules
from netparser import netparse
from superqkdnode import SuperQKDNode
from srqkdnode import SRQKDNode
from newqkdtopo import NewQKDTopo
from messaging import MessagingProtocol
from keymanager import KeyManager
from logger import Logger
from keys_exception import NoMoreKeysException


def gen_network(filepath, nodes_number):
    G = nx.random_internet_as_graph(nodes_number)
    # G =  nx.path_graph(nodes_number) this is to generate the chain
    json_G = nx.node_link_data(G)
    with open(filepath, 'w') as f:
        json.dump(json_G, f, ensure_ascii=False)
    return G


def draw_to_file(graph, filepath):
    pos = nx.kamada_kawai_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=50, margins=0.01)
    nx.draw_networkx_labels(graph, pos, font_size=5, font_color='w')
    nx.draw_networkx_edges(graph, pos, width=0.5)
    plt.savefig(filepath, dpi=500, orientation='landscape',
                bbox_inches='tight')


def read_config(filepath):
    return QKDTopo(filepath)


def gen_topology(network, timeline, fidelity):
    sim_nodes = {}

    # construct dictionary of super qkd nodes
    for node in network.get_nodes_by_type(QKDTopo.QKD_NODE):
        sim_nodes[node.name] = SuperQKDNode(node.name)

    # make network topology with our wrappers
    for _, node in enumerate(network.get_nodes_by_type(QKDTopo.QKD_NODE)):
        for key in node.cchannels.keys():

            source = node.name
            dest = node.cchannels[key].receiver

            sender_name = source + " to " + dest + ".sender"
            sender = QKDNode(sender_name, timeline)

            receiver_name = source + " to " + dest + ".receiver"
            receiver = QKDNode(receiver_name, timeline)

            dest_receiver = dest + " to " + source + ".receiver"
            dest_sender = dest + " to " + source + ".sender"

            # sender channels
            cchannel_name = "cchannel[" + source + " to " + dest + ".sender]"
            cchannel = ClassicalChannel(cchannel_name, timeline, 1000, 1)
            cchannel.set_ends(sender, dest_receiver)

            qchannel_name = "qchannel[" + source + " to " + dest + ".sender]"
            qchannel = QuantumChannel(
                qchannel_name, timeline, 0.0001, 1000, fidelity)
            qchannel.set_ends(sender, dest_receiver)

            # receiver channels
            cchannel_name = "cchannel[" + source + " to " + dest + ".receiver]"
            cchannel = ClassicalChannel(cchannel_name, timeline, 1000, 1)
            cchannel.set_ends(receiver, dest_sender)

            qchannel_name = "qchannel[" + source + " to " + dest + ".receiver]"
            qchannel = QuantumChannel(
                qchannel_name, timeline, 0.0001, 1000, fidelity)
            qchannel.set_ends(receiver, dest_sender)

            senderp = MessagingProtocol(
                sender, "msgp", "msgp", dest_receiver, sim_nodes[node.name])
            receiverp = MessagingProtocol(
                receiver, "msgp", "msgp", dest_sender, sim_nodes[node.name])

            sim_nodes[node.name].srqkdnodes[dest] = SRQKDNode(
                sender, receiver, senderp, receiverp)

    return sim_nodes


def run_sim(timeline, network, sim_nodes, num_keys, key_size, delta):

    tick = time.time()
    print(f"{Fore.LIGHTMAGENTA_EX}[NODES PAIRED FOR QKD]{Fore.RESET}")

    # pair each directly connected QKDNode for the QKD
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

    # set up key managers for storing the generated quantum keys
    for super_node in sim_nodes.values():
        for srnode in super_node.srqkdnodes.values():
            km1 = KeyManager(timeline, key_size, num_keys)
            km1.lower_protocols.append(srnode.sender.protocol_stack[1])
            srnode.sender.protocol_stack[1].upper_protocols.append(km1)

            km2 = KeyManager(timeline, key_size, num_keys)
            km2.lower_protocols.append(srnode.receiver.protocol_stack[1])
            srnode.receiver.protocol_stack[1].upper_protocols.append(km2)

            srnode.addKeyManagers(km1, km2)

    # pick a random destination node for each node in the network

    sender_receiver = []
    for sender in sim_nodes:
        sender_node = int(sender[4:])
        receiver_node = random.randint(0, len(list(sim_nodes))-1)

        while sender_node == receiver_node:
            receiver_node = random.randint(0, len(list(sim_nodes))-1)

        sender_receiver.append({sender: f"node{receiver_node}"})

    print(
        f"{Fore.YELLOW}[Messages to Send]:{Fore.RESET} {json.dumps(sender_receiver, indent=4)}")

    # execute qkd for every node in the network
    timeline.init()
    for super_node in sim_nodes.values():
        for sr_node in super_node.srqkdnodes.values():
            print(
                f"{Fore.LIGHTCYAN_EX}[SEND QKD REQUEST]:{Fore.RESET} {sr_node.sender.name}")
            sr_node.senderkm.send_request()
    timeline.run()

    print(
        f"{Fore.YELLOW}[Simulation Time]:{Fore.RESET} {timeline.now() * (10**-12)} s")

    # generate the routing tables
    topo_manager = NewQKDTopo(sim_nodes)
    topo_manager.gen_forward_tables()

    num_nodes = len(sim_nodes)

    plaintext = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    successes = 0
    losses = 0

    i = 0
    
    # schedule messages and single key random QKD requests
    while timeline.now() + delta < timeline.stop_time:
        curr_sim_time = timeline.now()
        for key, value in sender_receiver[i % num_nodes].items():
            sender = key
            receiver = value
        i += 1
        try:
            message = {"dest": receiver, "payload": plaintext}
            message = json.dumps(message)
            timeline.init()

            print(
                f"{Fore.LIGHTCYAN_EX}[Message]:{Fore.RESET} {sender} to {receiver}")
            sim_nodes[sender].sendMessage(timeline, receiver, message)

            timeline.run()

        except NoMoreKeysException:
            losses += 1
        else:
            successes += 1

        # schedule QKD requests in between messages
        while timeline.now() - curr_sim_time < delta:
            timeline.init()
            qkd_num = random.randint(0, len(list(sim_nodes))-1)

            for i in range(0, qkd_num):
                node1 = random.randint(0, len(list(sim_nodes))-1)
                node_index = random.randint(
                    0, len(sim_nodes[f"node{node1}"].srqkdnodes.keys())-1)
                node2 = list(sim_nodes[f"node{node1}"].srqkdnodes.keys())[
                    node_index]
                print(
                    f"{Fore.LIGHTCYAN_EX}[SEND QKD REQUEST]:{Fore.RESET}"
                    f"{sim_nodes[f'node{node1}'].srqkdnodes[node2].sender.name}")

                # reset num keys internal to the stack protocol
                sim_nodes[f"node{node1}"].srqkdnodes[node2].sender.protocol_stack[1].frame_num = 1
                sim_nodes[node2].srqkdnodes[f"node{node1}"].receiver.protocol_stack[1].frame_num = 1

                sim_nodes[f"node{node1}"].srqkdnodes[node2].senderkm.send_request()

            timeline.run()

    print(
        f"{Fore.YELLOW}[Successful Messages]:{Fore.RESET} {successes}")
    print(
        f"{Fore.YELLOW}[Dropped Messages]:{Fore.RESET} {losses}")
    print(
        f"{Fore.YELLOW}[Simulation Time]:{Fore.RESET} {timeline.now() * (10**-12)} s")
    print(
        f"{Fore.YELLOW}[Execution Time]: {Fore.RESET} {(time.time() - tick):0.4f} s")

    for super_node in sim_nodes.values():
        for sr_node in super_node.srqkdnodes.values():
            sr_node.senderMetrics()


def main(argv):

    current_sim = "simulations/sim_" + \
        str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "/"
    filename = 'graph_networkx.json'
    parsename = 'graph_sequence.json'

    # default parameters of simulations
    num_keys = 3
    key_size = 128
    do_gen = True
    fidelity = 0.97
    nodes_number = 10
    output_html = False
    delta = 1  # 1 second
    end_time = 5  # 5 seconds

    # parse cli arguments
    opts, _ = getopt.getopt(argv, "f:n:s:kvq:d:e:ht:")
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
        # number of nodes to generate
        elif opt in ['-d']:
            nodes_number = int(arg)
        # max simulation duration in seconds
        elif opt in ['-e']:
            end_time = int(arg)
        # generate html output
        elif opt in ['-h']:
            output_html = True
        # set delta
        elif opt in ['-t']:
            delta = float(arg)

    # conversion of times to picoseconds
    end_time = end_time * (10**12)
    delta = delta * (10**12)

    # generate current sim folder and redirect output to the logger
    os.makedirs(os.path.dirname(current_sim), exist_ok=True)
    sys.stdout = Logger(current_sim + "sim_output.txt")

    print(
        f"{Fore.YELLOW}[Simulation Command]:{Fore.RESET} python3 {' '.join(sys.argv[0:])}")

    # generate random network
    if do_gen:
        print(
            f"{Fore.YELLOW}[Random Network Topology Generated]{Fore.CYAN}")
        graph = gen_network(current_sim + filename, nodes_number)
        while len(graph.nodes()) < 2:
            graph = gen_network(current_sim + filename, nodes_number)
    # load network from JSON
    else:
        print(
            f"{Fore.YELLOW}[Loaded Network Graph From File]:{Fore.RESET} {filename}")
        with open(filename, 'r') as f:
            js_graph = json.load(f)
        graph = nx.readwrite.json_graph.node_link_graph(js_graph)
        filename = 'graph_networkx.json'
        with open(current_sim + filename, 'w') as f:
            json.dump(js_graph, f, ensure_ascii=False)

    # save the network graph to png file
    draw_to_file(graph, current_sim + "network_graph.png")

    # parse NetworkX JSON to SeQUenCe JSON and load it
    netparse(current_sim + filename, current_sim + parsename)
    network = read_config(current_sim + parsename)

    # set up the network with our wrappers and run the simulation
    timeline = Timeline(end_time)
    sim_nodes = gen_topology(network, timeline, fidelity)
    run_sim(timeline, network, sim_nodes, num_keys, key_size, delta)

    sys.stdout.flush()
    if output_html:
        os.system("cat " + current_sim + "sim_output.txt"
                  + " | aha --black > " + current_sim + "sim_output.html")


if __name__ == "__main__":
    main(sys.argv[1:])
