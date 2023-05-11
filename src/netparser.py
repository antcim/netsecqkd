import json

def netparse(filepath, savepath):
    with open(filepath, 'r') as f:
        dict = json.load(f)

    nodes = dict['nodes']
    nodes_list = []
    for n in nodes:
        node_dict = {
            'name': 'node' + str(n['id']),
            'type': 'QKDNode',
            'seed': 0,
            'memo_size': 50
        }
        nodes_list.append(node_dict)

    links = dict['links']
    qchannels_list = []
    cchannels_list = []
    count = 0
    for l in links:
        # Left to right
        qchannel_dict = {
            'name': 'qchannel' + str(count) + '_' 
                + str(l['source']) + 'to' + str(l['target']),
            'source': 'node' + str(l['source']),
            'destination': 'node' + str(l['target']),
            'attenuation': 0.00001,
            'distance': 1000
        }
        qchannels_list.append(qchannel_dict)

        cchannel_dict = {
            'name': 'cchannel' + str(count) + '_' 
                + str(l['source']) + 'to' + str(l['target']),
            'source': 'node' + str(l['source']),
            'destination': 'node' + str(l['target']),
            'distance': 1000
        }
        cchannels_list.append(cchannel_dict)

        # Right to left
        qchannel_dict = {
            'name': 'qchannel' + str(count) + '_' 
                + str(l['target']) + 'to' + str(l['source']),
            'source': 'node' + str(l['target']),
            'destination': 'node' + str(l['source']),
            'attenuation': 0.00001,
            'distance': 1000
        }
        qchannels_list.append(qchannel_dict)    

        cchannel_dict = {
            'name': 'cchannel' + str(count) + '_' 
                + str(l['target']) + 'to' + str(l['source']),
            'source': 'node' + str(l['target']),
            'destination': 'node' + str(l['source']),
            'distance': 1000
        }
        cchannels_list.append(cchannel_dict)

        count += 1

    dict = {}
    dict['is_parallel'] = False
    dict['stop_time'] = 5000000000000
    dict['nodes'] = nodes_list
    dict['qchannels'] = qchannels_list
    dict['cchannels'] = cchannels_list

    with open(savepath, 'w') as f:
        f.write(json.dumps(dict, indent=4))
