from sequence.kernel.process import Process
from sequence.kernel.event import Event

from colorama import Fore


class SRQKDNode:
    def __init__(self, sender, receiver, senderp, receiverp):
        # nodes
        self.sender = sender
        self.receiver = receiver
        # messaging protocols for the nodes
        self.senderp = senderp
        self.receiverp = receiverp
        
    def addKeyManagers(self, senderkm, receiverkm):
        self.senderkm = senderkm
        self.receiverkm  = receiverkm
        self.senderp.addkm(senderkm)
        self.receiverp.addkm(receiverkm)

    def sendMessage(self, tl, plaintext):
        if len(self.senderkm.keys) > 0:
            key = self.senderkm.consume()
            process = Process(self.senderp, "start", [plaintext, key])
            event = Event(tl.time * 1e9, process)
            tl.schedule(event)
        else:
            print(Fore.RED, "[No More Keys To Use]", Fore.RESET)
            