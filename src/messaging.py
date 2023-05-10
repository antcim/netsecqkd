from enum import Enum, auto
import re

class MsgType(Enum):
    TEXT_MESS = auto()

from sequence.topology.node import Node
from sequence.protocol import Protocol
from sequence.message import Message

import onetimepad
from colorama import Fore

class MessagingProtocol(Protocol):
    def __init__(self, own: Node, name: str, other_name: str, other_node: str, superQKD):
        super().__init__(own, name)
        self.own = own
        own.protocols.append(self)
        self.other_name = other_name
        self.other_node = other_node
        self.superQKD = superQKD

    def init(self):
        pass

    def start(self, text: str, key: str):
        ciphertext = onetimepad.encrypt(text, key)
        new_msg = Message(MsgType.TEXT_MESS, self.other_name)
        new_msg.payload = ciphertext
        new_msg.protocol_type = type(self)
        self.own.send_message(self.other_node, new_msg)

    def received_message(self, src: str, message: Message):
        assert message.msg_type == MsgType.TEXT_MESS
        plaintext = onetimepad.decrypt(message.payload, self.km.consume())

        if plaintext.startswith(self.superQKD.name + ":"):

            print(Fore.LIGHTMAGENTA_EX + "[" + self.own.name + "]" + Fore.RESET)
            print("Received: " + Fore.LIGHTGREEN_EX + "TEXT Message " + Fore.RESET)
            print("At Time: " + Fore.LIGHTCYAN_EX + str(self.own.timeline.now()) + Fore.RESET)
            print("Encrypted Message: " + Fore.LIGHTYELLOW_EX + message.payload + Fore.RESET)
            print("Decrypted Message: " + Fore.LIGHTYELLOW_EX + plaintext + Fore.RESET + "\n")

        # Forwarding del messaggio
        else:
            dst = re.search(r'node\d+', plaintext).group()
            print(Fore.LIGHTMAGENTA_EX + "[" + self.own.name + "]" + Fore.RESET)
            print("Received: " + Fore.LIGHTGREEN_EX + "TEXT Message " + Fore.RESET)
            print("At Time: " + Fore.LIGHTCYAN_EX + str(self.own.timeline.now()) + Fore.RESET)
            print("Encrypted Message: " + Fore.LIGHTYELLOW_EX + message.payload + Fore.RESET)
            print("Decrypted Message: " + Fore.LIGHTYELLOW_EX + plaintext + Fore.RESET)
            print(Fore.LIGHTBLUE_EX + "[Forwarding...]\n" + Fore.RESET)
            self.superQKD.sendMessage(self.own.timeline, dst, plaintext)


    def addkm(self, km):
        self.km = km