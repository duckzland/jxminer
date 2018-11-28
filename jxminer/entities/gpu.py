import math, subprocess

class GPU:

    """
        This is the base class for GPU instance
    """

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
        if kwargs.get('fan', False):
            self.setFanLevel(self.round(kwargs.get('fan')))

        if kwargs.get('core', False):
            self.setCoreLevel(self.round(kwargs.get('core')))

        if kwargs.get('memory', False):
            self.setMemoryLevel(self.round(kwargs.get('memory')))

        if kwargs.get('power', False):
            self.setPowerLevel(self.round(kwargs.get('power')))


    def isNotAtLevel(self, type, level):
        return getattr(self, "%sLevel" % type) != level


    def setFanLevel(self, level):
        pass

    def setCoreLevel(self, level):
        pass

    def setMemoryLevel(self, level):
        pass

    def setPowerLevel(self, level):
        pass