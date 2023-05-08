## Dev Guide
Timeline letta da json non utilizzabile per la simulazione con i nodi wrapper.

Chiavi generate possiblilmente diverse se la fidelity dei canali quantistici < 1.


## To do
- mandare messaggi tra nodi direttamente collegati

- cifare i messaggi

# errors in receive_message function of QKDNode in node.py of sequence lib
if type(protocol) == msg.protocol_type:
                protocol.received_message(src, msg)
                return

POSSIBLE LIBRARY ERROR?
this compares a type with a string which will never match!

this is a fix for it

if protocol.name == "receiverp" or protocol.name == "senderp":
    protocol.received_message(src, msg)
    return
