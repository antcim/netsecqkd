class KeyManager():
    def __init__(self, timeline, keysize, num_keys):
        self.timeline = timeline
        self.lower_protocols = []
        self.keysize = keysize
        self.num_keys = num_keys
        self.keys = []
        self.times = []

    def send_request(self):
        for p in self.lower_protocols:
            # interface for BB84 to generate key
            p.push(self.keysize, self.num_keys)

    def pop(self, info):  # interface for BB84 to return generated keys
        self.keys.append(info)
        self.times.append(self.timeline.now() * 1e-9)

    def consume(self) -> str:
        key_format = "{0:0"+str(self.keysize)+"b}"
        return key_format.format(self.keys.pop(0))