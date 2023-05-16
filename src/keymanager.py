class KeyManager():

    def __init__(self, timeline, keysize, num_keys):
        self.timeline = timeline
        self.lower_protocols = []
        self.keysize = keysize
        self.num_keys = num_keys
        self.keys = []
        self.times = []
        self.requested = False

    def send_request(self):
        if self.requested:
            return
        self.requested = True
        for p in self.lower_protocols:
            p.push(self.keysize, self.num_keys)

    def pop(self, key):
        self.keys.append(key)
        self.times.append(self.timeline.now() * 1e-9)
        if self.num_keys == len(self.keys):
            self.requested = False

    def consume(self) -> str:
        key_format = "{0:0" + str(self.keysize) + "b}"
        return key_format.format(self.keys.pop(0))
    