from enum import Enum, auto
import json
from sequence.topology.node import Node
from sequence.protocol import Protocol
from sequence.message import Message
import onetimepad
from colorama import Fore


class MsgType(Enum):

    TEXT_MESS = auto()


class MessagingProtocol(Protocol):

    def __init__(
            self, own: Node, name: str,
            other_name: str, other_node: str, superQKD):
        super().__init__(own, name)
        self.own = own
        own.protocols.append(self)
        self.other_name = other_name
        self.other_node = other_node
        self.super_qkd = superQKD
        self.km = None

    def init(self):
        pass

    def start(self, text: str, key: str):
        message = json.loads(text)
        ciphertext = onetimepad.encrypt(message["payload"], key)
        message["payload"] = ciphertext
        new_msg = Message(MsgType.TEXT_MESS, self.other_name)
        new_msg.payload = json.dumps(message)
        new_msg.protocol_type = type(self)
        self.own.send_message(self.other_node, new_msg)

    def received_message(self, src: str, msg: Message):
        assert msg.msg_type == MsgType.TEXT_MESS

        packet = json.loads(msg.payload)
        plaintext = onetimepad.decrypt(packet["payload"], self.km.consume())

        if packet["dest"] == self.super_qkd.name:
            print(f"{Fore.LIGHTMAGENTA_EX}[{self.own.name}]{Fore.RESET}")
            print(f"Received: {Fore.LIGHTGREEN_EX}TEXT Message{Fore.RESET}")
            print(
                f"At Simulation Time: {Fore.LIGHTCYAN_EX}{self.own.timeline.now()} ps{Fore.RESET}")
            print(
                f"Encrypted Message: {Fore.LIGHTYELLOW_EX}{packet['payload']}{Fore.RESET}")
            print(
                f"Decrypted Message: {Fore.LIGHTYELLOW_EX}{plaintext}{Fore.RESET}")

        # Message forwarding
        else:
            packet["payload"] = plaintext
            print(f"{Fore.LIGHTMAGENTA_EX}[{self.own.name}]{Fore.RESET}")
            print(f"Received: {Fore.LIGHTGREEN_EX}TEXT Message{Fore.RESET}")
            print(
                f"At Simulation Time: {Fore.LIGHTCYAN_EX}{self.own.timeline.now()} ps{Fore.RESET}")
            print(f"{Fore.LIGHTBLUE_EX}[Forwarding...]{Fore.RESET}\n")
            self.super_qkd.sendMessage(self.own.timeline, packet["dest"],
                                       json.dumps(packet))

    def addkm(self, km):
        self.km = km
