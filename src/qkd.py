from ipywidgets import interact
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
            p.push(self.keysize, self.num_keys) # interface for BB84 to generate key
            
    def pop(self, info): # interface for BB84 to return generated keys
        self.keys.append(info)
        self.times.append(self.timeline.now() * 1e-9)


def test(sim_time, keysize):
    """
    sim_time: duration of simulation time (ms)
    keysize: size of generated secure key (bits)
    """

    network_config = "src/testnet.json"
    network_topo = QKDTopo(network_config)
    print(network_topo.get_qchannels())
    tl = network_topo.get_timeline()
    
    n1 = network_topo.get_nodes_by_type(QKDTopo.QKD_NODE)[0]
    # print(n1.qchannels())
    n2 = network_topo.get_nodes_by_type(QKDTopo.QKD_NODE)[1]
    n1.set_seed(0)
    n2.set_seed(1)
    pair_bb84_protocols(n1.protocol_stack[0], n2.protocol_stack[0])

    cc0 = network_topo.get_cchannels()[0]
    cc1 = network_topo.get_cchannels()[1]
    qc0 = network_topo.get_qchannels()[0]
    qc1 = network_topo.get_qchannels()[1]
    qc0.polarization_fidelity = 0.97
    qc1.polarization_fidelity = 0.97
    
    # instantiate our written keysize protocol
    km1 = KeyManager(tl, keysize, 25)
    km1.lower_protocols.append(n1.protocol_stack[0])
    n1.protocol_stack[0].upper_protocols.append(km1)
    km2 = KeyManager(tl, keysize, 25)
    km2.lower_protocols.append(n2.protocol_stack[0])
    n2.protocol_stack[0].upper_protocols.append(km2)
    
    # start simulation and record timing
    tl.init()
    km1.send_request()
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

test(5000, 128)