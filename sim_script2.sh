#! /bin/bash

# Rate 0.00125
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.00125 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.00125 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.00125 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.00125 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.00125 -e 1
wait

# Rate 0.001
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001 -e 1
wait
python3 src/qkd_sim.py -f graph_networkx_chain.json -n 5 -s 128 -h -t 0.001 -e 1
wait