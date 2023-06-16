# Network Security Project: QKD

Each run will generate a folder in the `sim directory`.

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
- \-d
    - the number of nodes composing the network we want to test
    - default: 10
- \-n \<int> 
    - the number of keys to generate per each QKD instance
    - default: 3
- \-s \<int> 
    - the number bits of each key to generate per each QKD instance
    - default: 128
- \-q <float, 0 < n <=1> 
    - fidelity of the quantum channels
    - default: 0.97
- \-t 
    - set delta time of the messages in seconds
- \-e 
    - set end time of the destination in seconds
- \-k 
    - print generated/remaining keys
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