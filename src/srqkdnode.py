from sequence.kernel.process import Process
from sequence.kernel.event import Event
from colorama import Fore
from keys_exception import NoMoreKeysException
from nop import Nop
from key_cont import KeyConteiner

class SRQKDNode:
    
    drop = 0

    def __init__(self, sender, receiver, senderp, receiverp):
        # Nodes
        self.sender = sender
        self.receiver = receiver

        # Messaging protocols for the nodes
        self.senderp = senderp
        self.receiverp = receiverp

    def addKeyManagers(self, senderkm, receiverkm):
        self.senderkm = senderkm
        self.receiverkm = receiverkm
        self.senderp.addkm(senderkm)
        self.receiverp.addkm(receiverkm)

    def sendMessage(self, tl, plaintext, delta):
        if len(KeyConteiner.keys[self.sender.name]) > 0:
            key = self.senderkm.consume()
            process = Process(self.senderp, "start", [plaintext, key])
            event = Event(tl.now() + delta, process)
            tl.schedule(event)
            return
        SRQKDNode.drop += 1
        # dummy event necessary for correct scheduling
        nop = Nop()
        process = Process(nop, "nop", [])
        event = Event(tl.now() + delta, process)
        tl.schedule(event)
        
        print(f"{Fore.RED} sender.name = {self.sender.name}{Fore.RESET}")
        print(Fore.RED, "[No Keys Available To Use]", Fore.RESET)
        return

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
