# Network Security Project: QKD

## Dev File Guide
The project is contained into `qkd_sim.py`.

sim
    sim num...
        graph_networkx.json
        graph_sequence.json
        network_graph.png
        sim_output.txt
        sim_output.html

## CLI Arguments
- \-f read network graph topology from json file
- \-n the number of key to generate per each QKD instance
- \-s the number bits of each key to generate per each QKD instance
- \-q fidelity of the quantum channels
- \-e print error rates
- \-k print generated/remaining keys
- \-v verbose printing of the network and pairing setup

## Dependencies List
networkx

sequence