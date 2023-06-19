#! /bin/bash

# Rate 0.0025 
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.0025 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.0025 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.0025 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.0025 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.0025 -e 1
wait

# Rate 0.001667
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001667 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001667 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001667 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001667 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001667 -e 1
wait