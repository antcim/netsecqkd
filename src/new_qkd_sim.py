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
import threading
from threading import Event
from key_cont import KeyConteiner


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
    # G =  nx.path_graph(nodes_number) this is to generate the chain
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
            
            KeyConteiner.keys[sender_name] = []
            KeyConteiner.keys[receiver_name] = []


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

def run_setup(tl, network, sim_nodes, num_keys, key_size):
    tick = time.time()
    print(f"{Fore.LIGHTMAGENTA_EX}[NODES PAIRED FOR QKD]{Fore.RESET}")
    
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
            km1 = KeyManager(tl, srnode.sender, key_size, num_keys)
            km1.lower_protocols.append(srnode.sender.protocol_stack[1])
            srnode.sender.protocol_stack[1].upper_protocols.append(km1)

            km2 = KeyManager(tl, srnode.receiver, key_size, num_keys)
            km2.lower_protocols.append(srnode.receiver.protocol_stack[1])
            srnode.receiver.protocol_stack[1].upper_protocols.append(km2)

            srnode.addKeyManagers(km1, km2)

    # Start simulation and record timing
    # Generate routing tables
    topo_manager = NewQKDTopo(sim_nodes)
    
    # execute qkd for every node in the network
    tl.init()
    for super_node in sim_nodes.values():
        for sr_node in super_node.srqkdnodes.values():
            print(f"{Fore.LIGHTCYAN_EX}[SEND QKD REQUEST]:{Fore.RESET} {sr_node.sender.name}")
            sr_node.senderkm.send_request()
    tl.run()
    
    topo_manager.gen_forward_tables()
    

def runSim_mess(tl, network, sim_nodes, num_keys, key_size, delta):

    tick = time.time()
    
    # pick a destination node for each node in the network
    sender_receiver = []
    for sender in sim_nodes:
        sender_node = int(sender[4:])
        receiver_node = random.randint(0, len(list(sim_nodes))-1)

        while sender_node == receiver_node:
            receiver_node = random.randint(0, len(list(sim_nodes))-1)

        sender_receiver.append({sender: f"node{receiver_node}"})

    print(f"{Fore.YELLOW}[Messages to Send]:{Fore.RESET} {json.dumps(sender_receiver, indent=4)}")

    # Generate the message with the destination
    plaintext = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    successes = 0
    losses = 0

    i = 0
    num_nodes = len(sim_nodes)
    
    while tl.now() + delta <= tl.stop_time:
        for key, value in sender_receiver[i % num_nodes].items():
            sender = key
            receiver = value
        i += 1
        
        message = {"dest": receiver, "payload": plaintext}
        message = json.dumps(message)
        tl.init()

        print(f"{Fore.LIGHTCYAN_EX}[Message]:{Fore.RESET} {sender} to {receiver}")
        sim_nodes[sender].sendMessage(tl, receiver, message, delta)
        
        tl.run()
        time.sleep(20)
        
        
    
    print(
        f"{Fore.YELLOW}[Successful Messages]:{Fore.RESET} {MessagingProtocol.succ}")
    print(
        f"{Fore.YELLOW}[Dropped Messages]:{Fore.RESET} {SuperQKDNode.drop + SRQKDNode.drop}")
    print(
        f"{Fore.YELLOW}[Simulation Time]:{Fore.RESET} {tl.now() * (10**-12)} s")
    print(
        f"{Fore.YELLOW}[Execution Time]: {Fore.RESET} {(time.time() - tick):0.4f} s")
    

def runSim_qkd(tl, network, sim_nodes, num_keys, key_size, delta, event):
    tick = time.time()
    #print(f"{Fore.LIGHTMAGENTA_EX}[NODES PAIRED FOR QKD]{Fore.RESET}")
    
    for node in network.get_nodes_by_type(QKDTopo.QKD_NODE):
        neighbors = node.qchannels.keys()
        for k in neighbors:
            A = sim_nodes[node.name].srqkdnodes[k].sender
            B = sim_nodes[k].srqkdnodes[node.name].receiver

            A.set_seed(0)
            B.set_seed(1)

            pair_bb84_protocols(A.protocol_stack[0], B.protocol_stack[0])
            pair_cascade_protocols(A.protocol_stack[1], B.protocol_stack[1])
            #print(
            #    f"{Fore.GREEN}[PAIR]: {Fore.RESET}"
            #    f"{Fore.LIGHTCYAN_EX}[{A.name}]{Fore.RESET}"
            #    f" - {Fore.LIGHTBLUE_EX}[{B.name}]{Fore.RESET}")

    # this might be unnecessary with the cascade protocol
    for super_node in sim_nodes.values():
        for srnode in super_node.srqkdnodes.values():
            km1 = KeyManager(tl, srnode.sender, key_size, num_keys)
            km1.lower_protocols.append(srnode.sender.protocol_stack[1])
            srnode.sender.protocol_stack[1].upper_protocols.append(km1)

            km2 = KeyManager(tl, srnode.receiver, key_size, num_keys)
            km2.lower_protocols.append(srnode.receiver.protocol_stack[1])
            srnode.receiver.protocol_stack[1].upper_protocols.append(km2)

            srnode.addKeyManagers(km1, km2)

    # execute qkd for every node in the network
    while not event.is_set():
        
        for super_node in sim_nodes.values():
            for sr_node in super_node.srqkdnodes.values():
                
                #print(f"{Fore.LIGHTCYAN_EX}[SEND QKD REQUEST]:{Fore.RESET} {sr_node.sender.name}")
                sr_node.sender.protocol_stack[1].frame_num = 1
                sr_node.receiver.protocol_stack[1].frame_num = 1
                print(
                    f"{Fore.YELLOW}[START QKD]")  
                tl.init()
                sr_node.senderkm.send_request()
                tl.run()
                print(
                    f"{Fore.YELLOW}[END QKD]")  

    #print(
    #    f"{Fore.YELLOW}[Simulation Time]:{Fore.RESET} {tl.now() * (10**-12)} s")
    #print(
    #    f"{Fore.YELLOW}[Execution Time]: {Fore.RESET} {(time.time() - tick):0.4f} s")
    
    # for super_node in sim_nodes.values():
    #     for sr_node in super_node.srqkdnodes.values():
    #         sr_node.senderMetrics()
    

def main(argv):

    current_sim = "simulations/sim_" + \
        str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S")) + "/"
    num_keys = 3
    key_size = 128
    do_gen = True
    filename = 'graph_networkx.json'
    parsename = 'graph_sequence.json'
    fidelity = 0.97
    nodes_number = 10
    output_html = False
    delta = 1 # 1 second
    end_time = 5 # 5 seconds

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
            end_time = float(arg) + 0.000000001
        # generate html output
        elif opt in ['-h']:
            output_html = True
        # set delta
        elif opt in ['-t']:
            delta = float(arg)

    # conversion to picoseconds
    end_time = end_time * (10**12)
    delta = delta * (10**12)

    os.makedirs(os.path.dirname(current_sim), exist_ok=True)
    sys.stdout = Logger(current_sim + "sim_output.txt")

    print(f"{Fore.YELLOW}[Simulation Command]:{Fore.RESET} python3 {' '.join(sys.argv[0:])}")

    if do_gen:
        print(
            f"{Fore.YELLOW}[Random Network Topology Generated]{Fore.CYAN}")
        graph = genNetwork(current_sim + filename, nodes_number)
        while len(graph.nodes()) < 2:
            graph = genNetwork(current_sim + filename, nodes_number)
    else:
        print(
            f"{Fore.YELLOW}[Loaded Network Graph From File]:{Fore.RESET} {filename}")
        with open(filename, 'r') as f:
            js_graph = json.load(f)
        graph = nx.readwrite.json_graph.node_link_graph(js_graph)
        filename = 'graph_networkx.json'
        with open(current_sim + filename, 'w') as f:
            json.dump(js_graph, f, ensure_ascii=False)

    drawToFile(graph, current_sim + "network_graph.png")
    netparse(current_sim + filename, current_sim + parsename)
    network = readConfig(current_sim + parsename)

    tl_mess = Timeline(end_time)
    tl_qkd = Timeline()

    sim_nodes_mess = genTopology(network, tl_mess, fidelity)
    sim_nodes_qkd = genTopology(network, tl_qkd, fidelity)
    
    run_setup(tl_mess, network, sim_nodes_mess, num_keys, key_size)
    
    event = Event()
    
    th_mess = threading.Thread(target=runSim_mess, args=(tl_mess, network, sim_nodes_mess, num_keys, key_size, delta,))
    th_qkd = threading.Thread(target=runSim_qkd, args=(tl_qkd, network, sim_nodes_qkd, num_keys, key_size, delta, event,))
    
    th_qkd.start()
    th_mess.start()
    
    th_mess.join()
    
    if th_qkd.is_alive():
        event.set()
    
    print(KeyConteiner.keys.items())
    
    
    sys.stdout.flush()
    if output_html:
        os.system("cat " + current_sim + "sim_output.txt"
              + " | aha --black > " + current_sim + "sim_output.html")


if __name__ == "__main__":
    main(sys.argv[1:])