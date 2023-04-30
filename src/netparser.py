import json

def netparse(filepath, savepath):
    # READ JSON INTO DICT
    with open(filepath, 'r') as f:
        dict = json.load(f)

    # print(json.dumps(dict, indent = 4))

    # NODE
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

    # for x in nodes_list:
    # print(x)

    # LINK
    links = dict['links']
    qchannels_list = []
    cchannels_list = []
    count = 0
    for l in links:

        # sx to dx
        qchannel_dict = {
            'name': 'qchannel'+str(count)+'_'+str(l['source'])+'to'+ str(l['target']),
            'source': 'node' + str(l['source']),
            'destination': 'node' + str(l['target']),
            'attenuation': 0.00001,
            'distance': 1000
        }
        qchannels_list.append(qchannel_dict)

        cchannel_dict = {
            'name': 'cchannel'+str(count)+'_'+str(l['source'])+'to'+ str(l['target']),
            'source': 'node' + str(l['source']),
            'destination': 'node' + str(l['target']),
            'distance': 1000
        }
        cchannels_list.append(cchannel_dict)

        # dx to sx
        qchannel_dict = {
            'name': 'qchannel'+str(count)+'_'+str(l['target'])+'to'+ str(l['source']),
            'source': 'node' + str(l['target']),
            'destination': 'node' + str(l['source']),
            'attenuation': 0.00001,
            'distance': 1000
        }
        qchannels_list.append(qchannel_dict)    

        cchannel_dict = {
            'name': 'cchannel'+str(count)+'_'+str(l['target'])+'to'+ str(l['source']),
            'source': 'node' + str(l['target']),
            'destination': 'node' + str(l['source']),
            'distance': 1000
        }
        cchannels_list.append(cchannel_dict)

        count += 1

    # for x in qchannels_list:
    #  print(x)

    # for x in cchannels_list:
    #  print(x)

    # CREATE NEW DICT
    dict = {}
    dict['is_parallel'] = False
    dict['stop_time'] = 5000000000000
    dict['nodes'] = nodes_list
    dict['qchannels'] = qchannels_list
    dict['cchannels'] = cchannels_list

    # print(json.dumps(dict, indent = 4))

    # WRITE JSON
    with open(savepath, 'w') as f:
        f.write(json.dumps(dict, indent=4))
