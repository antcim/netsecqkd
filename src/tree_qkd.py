from matplotlib import pyplot as plt
import time

from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.qkd.BB84 import BB84
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
    
    n0.set_seed(0)
    n1.set_seed(1)
    n2.set_seed(2)

    pair_bb84_protocols(n0.protocol_stack[0], n2.protocol_stack[0])
    pair_bb84_protocols(n1.protocol_stack[0], n0.protocol_stack[0])

    # connect the nodes and set parameters for the fibers
    # note that channels are one-way
    # construct a classical communication channel
    # (with arguments for the channel name, timeline, and length (in m))
    cc0 = ClassicalChannel("cc_n0_n1", tl, distance=1e3)
    cc1 = ClassicalChannel("cc_n1_n0", tl, distance=1e3)

    cc2 = ClassicalChannel("cc_n2_n0", tl, distance=1e3)
    cc3 = ClassicalChannel("cc_n0_n2", tl, distance=1e3)

    cc4 = ClassicalChannel("cc_n1_n2", tl, distance=1e3)
    cc5 = ClassicalChannel("cc_n2_n1", tl, distance=1e3)
    
    cc0.set_ends(n0, n1.name)
    cc1.set_ends(n1, n0.name)

    cc2.set_ends(n2, n0.name)
    cc3.set_ends(n0, n2.name)

    cc4.set_ends(n1, n2.name)
    cc5.set_ends(n2, n1.name)
    
    # construct a quantum communication channel
    # (with arguments for the channel name, timeline, attenuation (in dB/km), and distance (in m))
    qc0 = QuantumChannel("qc_n0_n1", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc1 = QuantumChannel("qc_n1_n0", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)

    qc2 = QuantumChannel("qc_n2_n0", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc3 = QuantumChannel("qc_n0_n2", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)

    qc4 = QuantumChannel("qc_n1_n2", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc5 = QuantumChannel("qc_n2_n1", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)

    qc0.set_ends(n0, n1.name)
    qc1.set_ends(n1, n0.name)

    qc2.set_ends(n2, n0.name)
    qc3.set_ends(n0, n2.name)

    qc4.set_ends(n1, n2.name)
    qc5.set_ends(n2, n1.name)
   
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

    # start simulation and record timing
    tl.init()
    km1.send_request()
    tick = time.time()
    tl.run()

    print("execution time %.2f sec" % (time.time() - tick))
    print("key error rates:")
    for i, e in enumerate(n1.protocol_stack[0].error_rates):
        print("\tkey {}:\t{}%".format(i + 1, e * 100))

    tl.init()
    pair_bb84_protocols(n0.protocol_stack[0], n2.protocol_stack[0])
    km0.send_request()
    tick = time.time()
    tl.run()

    print("execution time %.2f sec" % (time.time() - tick))
    
    print("key error rates:")
    for i, e in enumerate(n0.protocol_stack[0].error_rates):
        print("\tkey {}:\t{}%".format(i + 1, e * 100))


old_test(5000, 128)