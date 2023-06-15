#! /bin/bash

# Rate 0.5 
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.5 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.5 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.5 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.5 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.5 -e 1
wait

# Rate 0.1
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.1 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.1 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.1 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.1 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.1 -e 1
wait

# Rate 0.05
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.05 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.05 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.05 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.05 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.05 -e 1
wait
