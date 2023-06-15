#! /bin/bash

# Rate 0.02
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.02 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.02 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.02 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.02 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.02 -e 1
wait

# Rate 0.01
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.01 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.01 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.01 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.01 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.01 -e 1
wait

# Rate 0.005
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.005 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.005 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.005 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.005 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.005 -e 1
wait
