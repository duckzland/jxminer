import time, threading, signal
from abc import ABCMeta, abstractmethod
#from entities import *

class Thread(threading.Thread):

    """
        This is the base class for all of the thread instance
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()


    @abstractmethod
    def init(self):
        pass


    @abstractmethod
    def update(self):
        pass


    @abstractmethod
    def destroy(self):
        pass


    def configure(self, **kwargs):

        self.function = self.update
        self.args = kwargs
        self.config = Config()
        self.buffers = dict()
        self.init()


    def run(self):
        while not self.shutdown_flag.is_set():
            self.function()

            for i in range(self.ticks):
                if not self.shutdown_flag.is_set():
                    time.sleep(1)


    def setPauseTime(self, tick):
        self.ticks = int(tick)


    def register(self, name, parent):
        self.name = name
        self.parent = parent


    def isActive(self):
        return not self.shutdown_flag.is_set()


    def isStopped(self):
        return self.shutdown_flag.is_set()


    def stop(self):
        self.shutdown_flag.set()


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
