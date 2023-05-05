from sequence.topology.node import QKDNode

class SuperQKDNode:
    def __init__(self, name):
        self.name = name
        self.srqkdnodes = []

    def addSRQKDNode(self, node):
        self.srqkdnodes.append(node)

