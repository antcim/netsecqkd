from colorama import Fore
from keys_exception import NoMoreKeysException

class SuperQKDNode:

    def __init__(self, name):
        self.name = name
        self.srqkdnodes = []
        self.routing_table = {}

    def addSRQKDNode(self, node):
        self.srqkdnodes.append(node)

    def sendMessage(self, tl, dest_node, plaintext_msg):
        if dest_node not in self.routing_table.keys():
            print(Fore.RED, "[No Path towards Destination]", Fore.RESET)
            print(Fore.RED, "[Run Another Simulation]", Fore.RESET)
            raise NoMoreKeysException
        else:
            next_hop_name = self.routing_table[dest_node][1]
            for srn in self.srqkdnodes:
                if srn.sender.name.endswith(next_hop_name + ".sender"):
                    srn.sendMessage(tl, plaintext_msg)
