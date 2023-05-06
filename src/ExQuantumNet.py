from matplotlib import pyplot as plt
import time

from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.topology.qkd_topo import QKDTopo

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
            p.push(self.keysize, self.num_keys) # Method to receive requests for key generation
            
    def pop(self, info): # interface for BB84 to return generated keys
        self.keys.append(info)
        self.times.append(self.timeline.now() * 1e-9)


def old_test(sim_time, keysize):
    """
    sim_time: duration of simulation time (ms)
    keysize: size of generated secure key (bits)
    """
    # begin by defining the simulation timeline with the correct simulation time
    tl = Timeline(sim_time * 1e9)
    
    # Here, we create nodes for the network (QKD nodes for key distribution)
    # stack_size=1 indicates that only the BB84 protocol should be included
    n0 = QKDNode("n0", tl, stack_size=1)
    n1 = QKDNode("n1", tl, stack_size=1)
    n2 = QKDNode("n2", tl, stack_size=1)
    n3 = QKDNode("n3", tl, stack_size=1)
    
    n0.set_seed(0)
    n1.set_seed(1)
    n2.set_seed(2)
    n3.set_seed(3)

    pair_bb84_protocols(n1.protocol_stack[0], n0.protocol_stack[0])
    pair_bb84_protocols(n2.protocol_stack[0], n3.protocol_stack[0])
    
    # connect the nodes and set parameters for the fibers
    # note that channels are one-way
    # construct a classical communication channel
    # (with arguments for the channel name, timeline, and length (in m))
    cc0 = ClassicalChannel("cc_n0_n1", tl, distance=1e3)
    cc1 = ClassicalChannel("cc_n1_n0", tl, distance=1e3)

    cc2 = ClassicalChannel("cc_n2_n3", tl, distance=1e3)
    cc3 = ClassicalChannel("cc_n3_n2", tl, distance=1e3)
    
    cc0.set_ends(n0, n1.name)
    cc1.set_ends(n1, n0.name)

    cc2.set_ends(n2, n3.name)
    cc3.set_ends(n3, n2.name)
    
    # construct a quantum communication channel
    # (with arguments for the channel name, timeline, attenuation (in dB/km), and distance (in m))
    qc0 = QuantumChannel("qc_n0_n1", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc1 = QuantumChannel("qc_n1_n0", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)

    qc2 = QuantumChannel("qc_n2_n3", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc3 = QuantumChannel("qc_n3_n2", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)

    qc0.set_ends(n0, n1.name)
    qc1.set_ends(n1, n0.name)

    qc2.set_ends(n2, n3.name)
    qc3.set_ends(n3, n2.name)
   
    # instantiate our written keysize protocol
    km0 = KeyManager(tl, keysize, 25)
    km0.lower_protocols.append(n0.protocol_stack[0])
    n0.protocol_stack[0].upper_protocols.append(km0)

    km1 = KeyManager(tl, keysize, 25)
    km1.lower_protocols.append(n1.protocol_stack[0])
    n1.protocol_stack[0].upper_protocols.append(km1)

    km2 = KeyManager(tl, keysize, 25)
    km2.lower_protocols.append(n2.protocol_stack[0])
    n2.protocol_stack[0].upper_protocols.append(km2)

    km3 = KeyManager(tl, keysize, 25)
    km3.lower_protocols.append(n3.protocol_stack[0])
    n3.protocol_stack[0].upper_protocols.append(km3)

    # start simulation and record timing
    tl.init()
    print("ciao")
    km1.send_request()
    km2.send_request()
    tick = time.time()
    tl.run()
    print("execution time %.2f sec" % (time.time() - tick))
    
    print("key error rates:")
    for i, e in enumerate(n1.protocol_stack[0].error_rates):
        print("\tkey {}:\t{}%".format(i + 1, e * 100))
    
    print("key error rates:")
    for i, e in enumerate(n2.protocol_stack[0].error_rates):
        print("\tkey {}:\t{}%".format(i + 1, e * 100))


def test(sim_time, keysize):
    """
    sim_time: duration of simulation time (ms)
    keysize: size of generated secure key (bits)
    """
    NUM_KEYS = 25

    network_config = "testnet.json"

    # Dal file json creo topologia, il costruttore parserà il json andando a creare un istanza QKDNode per ogni nodo di tipo QKDNode.
    network_topo = QKDTopo(network_config)
    tl = network_topo.get_timeline()
    
    QKDNodes = network_topo.get_nodes_by_type(QKDTopo.QKD_NODE)
    n1 = QKDNodes[0]
    n2 = QKDNodes[1]
    # Setta i seed dei nodi per riprodicibilità
    n1.set_seed(0)
    n2.set_seed(1)
    # Accoppia le istanze dei due nodi per il protoccolo BB84
    pair_bb84_protocols(n1.protocol_stack[0], n2.protocol_stack[0])

    #cc0 = network_topo.get_cchannels()[0]
    #cc1 = network_topo.get_cchannels()[1]

    for qc in network_topo.get_qchannels():
        qc.polarization_fidelity = 0.97
    
    # instantiate our written keysize protocol
    km1 = KeyManager(tl, keysize, NUM_KEYS)
    km1.lower_protocols.append(n1.protocol_stack[0])
    n1.protocol_stack[0].upper_protocols.append(km1)

    km2 = KeyManager(tl, keysize, NUM_KEYS)
    km2.lower_protocols.append(n2.protocol_stack[0])
    n2.protocol_stack[0].upper_protocols.append(km2)
    
    # start simulation and record timing
    tl.init()
    km1.send_request() # Nodo 1 invia richiesta per la generazione della chiave e l'avvio del protocollo
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

    print("Node 1 keys:")
    for i, key in enumerate(km1.keys):
        print("\t{0:0128b}".format(key))
    
    print("Node 2 keys:")
    for i, key in enumerate(km2.keys):
        print("\t{0:0128b}".format(key))

old_test(5000, 128)