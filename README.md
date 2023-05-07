# Network Security Project: QKD

## Dev File Guide
The project is contained into `qkd_sim.py`.

The `netparser.py` parses a random network generated with networkx to a sequance .json config file.

`parsed.json` is the output of the parser for the time being.

`testnet.json` is a two node network to test `qkd.py`with.

`rndNetConf.json` is the randomly generated network with networkx.

`bb84sequence.py` is a reference script from the sequence repo.

## CLI Argument
- \-f read topology from json config file
- \-nk the number of key to generate per each QKD instance
- \-nb the number bits of each key to generate per each QKD instance
- \-fq fidelity of the quantum channels
- \-e print error reates
- \-k print generated key
- \-v verbose printing of the network and pairing setup

## Dependencies List
networkx

sequence