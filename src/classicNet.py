from enum import Enum, auto

class MsgType(Enum):
    TEXT_MESS = auto()

from sequence.topology.node import Node
from sequence.protocol import Protocol
from sequence.message import Message

class SenderProtocol(Protocol):
    def __init__(self, own: Node, name: str, other_name: str, other_node: str):
        super().__init__(own, name)
        own.protocols.append(self)
        self.other_name = other_name
        self.other_node = other_node

    def init(self):
        pass

    def start(self):
        new_msg = Message(MsgType.TEXT_MESS, self.other_name)
        new_msg.payload = "GHESBORO"
        self.own.send_message(self.other_node, new_msg)

    def received_message(self, src: str, message: Message):
        assert message.msg_type == MsgType.TEXT_MESS
        print("node '{}' received TEXT message at time {}: {}".format(self.own.name, self.own.timeline.now(), message.payload))


class ReceiverProtocol(Protocol):
    def __init__(self, own: Node, name: str, other_name: str, other_node: str):
        super().__init__(own, name)
        own.protocols.append(self)
        self.other_name = other_name
        self.other_node = other_node
    
    def init(self):
        pass

    def received_message(self, src: str, message: Message):
        assert message.msg_type == MsgType.TEXT_MESS
        print("node '{}' received TEXT message at time {}: {}".format(self.own.name, self.own.timeline.now(), message.payload))
        new_msg = Message(MsgType.TEXT_MESS, self.other_name)
        new_msg.payload = "GHESBORO ANCHE A TE"
        self.own.send_message(self.other_node, new_msg)

from sequence.kernel.timeline import Timeline
from sequence.components.optical_channel import ClassicalChannel

tl = Timeline(1e12)

node1 = Node("node1", tl)
node2 = Node("node2", tl)
node3 = Node("node3", tl)

cc0 = ClassicalChannel("cc0", tl, 1e3, 1e9)
cc1 = ClassicalChannel("cc1", tl, 1e3, 1e9)

cc2 = ClassicalChannel("cc2", tl, 1e3, 1e9)
cc3 = ClassicalChannel("cc3", tl, 1e3, 1e9)

cc0.set_ends(node1, node2.name)
cc1.set_ends(node2, node1.name)

cc2.set_ends(node2, node3.name)
cc3.set_ends(node3, node2.name)

senderp = SenderProtocol(node1, "senderp", "receiverp", "node3")
receiverp = ReceiverProtocol(node3, "receiverp", "senderp", "node1")

from sequence.kernel.process import Process
from sequence.kernel.event import Event

process = Process(senderp, "start", [])
event = Event(0, process)
tl.schedule(event)

tl.init()
tl.run()