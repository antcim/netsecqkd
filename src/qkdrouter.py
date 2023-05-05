from sequence.kernel.timeline import Timeline
from sequence.topology.router_net_topo import QuantumRouter
from sequence.topology.qkd_topo import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.topology.topology import Topology

timeline = Timeline(3e12)
router = QuantumRouter("router0", timeline)
node = QKDNode("node0", timeline)

qchannel = QuantumChannel("qch0", timeline, 0.0001, 500)
cchannel = ClassicalChannel("cch0", timeline, 500, 1e15)

router.assign_qchannel(qchannel, node.name)
router.assign_cchannel(cchannel, node.name)
node.assign_qchannel(qchannel, router.name)
node.assign_cchannel(cchannel, router.name)

print(node.qchannels)
print(router.qchannels)
