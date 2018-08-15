import math, subprocess

class GPU:

    "This is the base class for GPU instance"

    def __init__(self, index):
        self.index = index
        self.init()
        self.detect()
        

    def round(self, number):
        return int(math.ceil(float(number)))


    def call(self, command, options):
        p = subprocess.Popen(command, env=options, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait
        return p


    def init(self):
        pass


    def detect(self):
        pass


    def reset(self):
        pass


    def tune(self, **kwargs):
        pass