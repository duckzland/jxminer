
from entities.logger import *

class Thread:

    def __init__(self, start, config):
        self.active = False
        self.job = False
        self.config = config
        self.buffers = dict()
        self.init()
        if start:
            self.start()


    def register(self, name, parent):
        self.name = name
        self.parent = parent


    def init(self):
        pass


    def start(self):
        try:
            if self.job:
                self.job.start()
        except:
            self.active = False

        finally:
            self.active = True


    def update(self, runner):
        pass


    def destroy(self):
        if self.job:
            self.job.shutdown_flag.set()
        self.active = False


    def check(self):
        try:
            if self.job:
                self.active = self.job.shutdown_flag.is_set()

        except:
            self.active = false

        finally:
            return self.active