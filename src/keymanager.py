from key_cont import KeyConteiner

class KeyManager():

    def __init__(self, timeline, own, keysize, num_keys):
        self.own = own
        self.timeline = timeline
        self.lower_protocols = []
        self.keysize = keysize
        self.num_keys = num_keys
        self.keys = []
        self.times = []

    def send_request(self):
        for p in self.lower_protocols:
            p.push(self.keysize, self.num_keys)

    def pop(self, key):
        KeyConteiner.keys[self.own.name].append(key)
        #self.keys.append(key)
        self.times.append(self.timeline.now() * 1e-9)

    def consume(self) -> str:
        key_format = "{0:0" + str(self.keysize) + "b}"
        return key_format.format(KeyConteiner.keys[self.own.name].pop(0))
    
