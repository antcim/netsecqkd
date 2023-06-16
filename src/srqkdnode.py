from sequence.kernel.process import Process
from sequence.kernel.event import Event
from colorama import Fore
from keys_exception import NoMoreKeysException


class SRQKDNode:

    def __init__(self, sender, receiver, senderp, receiverp):
        # Nodes
        self.sender = sender
        self.receiver = receiver

        # Messaging protocols for the nodes
        self.senderp = senderp
        self.receiverp = receiverp

        # Key Managers
        self.senderkm = None
        self.receiverkm = None

    def addKeyManagers(self, senderkm, receiverkm):
        self.senderkm = senderkm
        self.receiverkm = receiverkm
        self.senderp.add_key_manager(senderkm)
        self.receiverp.add_key_manager(receiverkm)

    def sendMessage(self, tl, plaintext):
        if len(self.senderkm.keys) > 0:
            key = self.senderkm.consume()
            process = Process(self.senderp, "start", [plaintext, key])
            event = Event(tl.now(), process)
            tl.schedule(event)
            return
        print(f"{Fore.RED} sender.name = {self.sender.name}{Fore.RESET}")
        print(Fore.RED, "[No Keys Available To Use]", Fore.RESET)
        raise NoMoreKeysException

    def _printMetrics(self, node):
        name = node.name
        bb84 = node.protocol_stack[0]
        cascade = node.protocol_stack[1]

        print(
            f"{Fore.LIGHTMAGENTA_EX}[Performance Metrics - {name}]{Fore.RESET}"
            f"\n{Fore.LIGHTCYAN_EX}Cascade Protocol{Fore.RESET}"
            f"\n\tThroughput: {cascade.throughput}bits/sec"
            f"\n\tError Bit Rate: {cascade.error_bit_rate}"
            f"\n\tLatency: {cascade.latency}"
            f"\n\tSetup Time: {cascade.setup_time}"
            f"\n\tStart Time: {cascade.start_time}"
            f"\n{Fore.LIGHTCYAN_EX}BB84 Protocol{Fore.RESET}"
            f"\n\tThroughput: {bb84.throughputs}bits/sec"
            f"\n\tError Rates: {bb84.error_rates}"
            f"\n\tLatency: {bb84.latency}s"
        )

    def senderMetrics(self):
        self._printMetrics(self.sender)

    def receiverMetrics(self):
        self._printMetrics(self.receiver)
