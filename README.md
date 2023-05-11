# Network Security Project: QKD
This project generates a random qkd network where all nodes are coupled in pairs.

Each pair than exchanges keys with the BB84 QKD protocol.

Every node contains a routing table to get to every other node.

The QKD keys are then used to cipher messages to be exchanged on the classical channel between the sender and receiver.

The used cipher is the One Time Pad.

For the message exchange we randomly pick two nodes among the available one and send a message from the first of these to the second.

Each run will generate a a folder in the `sim directory`.

**How to run the project**
```
python3 src/qkd_sim.py
```

### Simulations folder structure
- sim/
    - sim_year-month-day_hour_minute_second/
        - graph_networkx.json
        - graph_sequence.json
        - network_graph.png
        - sim_output.txt
        - sim_output.html

## CLI Arguments
- \-f \<filepath> 
    - read network topology from json file
    - if absent a random network will be generated
- \-n \<int> 
    - the number of keys to generate per each QKD instance
    - default: 3
- \-s \<int> 
    - the number bits of each key to generate per each QKD instance
    - default: 128
- \-q <float, 0 < n <=1> 
    - fidelity of the quantum channels
    - default: 1
- \-e 
    - print error rates
    - default: false
- \-k 
    - print generated/remaining keys
    - default: false
- \-v 
    - verbose printing of the network and pairing setup
    - default: false

## Dependencies List
### Python Libs
- networkx
- [sequence](https://github.com/sequence-toolbox/SeQUeNCe)
- [one time pad](https://github.com/albohlabs/one-time-pad)
- colorama

### Ascii to Html Adapter
```
$ sudo apt-get install aha
```