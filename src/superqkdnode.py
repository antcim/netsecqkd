from colorama import Fore
from keys_exception import NoMoreKeysException
from sequence.kernel.process import Process
from sequence.kernel.event import Event
from nop import Nop

class SuperQKDNode:
    
    drop = 0

    def __init__(self, name):
        self.name = name
        self.srqkdnodes = {}
        self.routing_table = {}

    def sendMessage(self, tl, dest_node, plaintext_msg, delta):
        if dest_node not in self.routing_table.keys():
            print(f"{Fore.RED}[No Path towards Destination]{Fore.RESET}")
            SuperQKDNode.drop += 1
            # dummy event necessary for correct scheduling
            nop = Nop()
            process = Process(nop, "nop", [])
            event = Event(tl.now() + delta, process)
            tl.schedule(event)
            return 
        else:
            next_hop_name = self.routing_table[dest_node][1]
            for srn in self.srqkdnodes.values():
                if srn.sender.name.endswith(next_hop_name + ".sender"):
                    srn.sendMessage(tl, plaintext_msg, delta)
