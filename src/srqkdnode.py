from sequence.topology.node import QKDNode

class SRQKDNode:
    def __init__(self, sender, receiver, senderp, receiverp):
        self.sender = sender
        self.receiver = receiver
        self.senderp = senderp
        self.receiverp = receiverp
