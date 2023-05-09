from enum import Enum, auto

class MsgType(Enum):
    TEXT_MESS = auto()

from sequence.topology.node import Node
from sequence.protocol import Protocol
from sequence.message import Message

import onetimepad

class MessagingProtocol(Protocol):
    def __init__(self, own: Node, name: str, other_name: str, other_node: str):
        super().__init__(own, name)
        self.own = own
        own.protocols.append(self)
        self.other_name = other_name
        self.other_node = other_node

    def init(self):
        pass

    def start(self, text, key):
        ciphertext = onetimepad.encrypt(text, key)
        new_msg = Message(MsgType.TEXT_MESS, self.other_name)
        new_msg.payload = ciphertext
        new_msg.protocol_type = type(self)
        self.own.send_message(self.other_node, new_msg)

    def received_message(self, src: str, message: Message):
        assert message.msg_type == MsgType.TEXT_MESS
        print("node '{}' received TEXT message at time {}: {}".format(self.own.name, self.own.timeline.now(), message.payload))