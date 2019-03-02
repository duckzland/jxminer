from abc import ABCMeta, abstractmethod

class Thread:

    """
        This is the base class for all of the thread instance
    """

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


    @abstractmethod
    def init(self):
        pass


    @abstractmethod
    def update(self, runner):
        pass


    def start(self):
        try:
            if self.job:
                self.job.start()
        except:
            self.active = False

        finally:
            self.active = True


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


# Registering all available thread instances
from casingFans import *
from cpuMiner import *
from feeRemoval import *
from gpuFans import *
from gpuMiner import *
from gpuTuner import *
from notification import *
from socketAction import *
from systemdWatchdog import *
from watchdog import *