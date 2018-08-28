import time, threading, signal

from entities.logger import *
from entities.shutdown import *

class Job(threading.Thread):

    """
        This is a class for defining a single Job instance
    """

    def __init__(self, ticks, func, *args):
        threading.Thread.__init__(self)
        self.setPauseTime(ticks)
        self.function = func
        self.args = args
        self.shutdown_flag = threading.Event()

    def run(self):
        while not self.shutdown_flag.is_set():
            self.function(self, *self.args)

            for i in range(self.ticks):
                if not self.shutdown_flag.is_set():
                    time.sleep(1)

    def setPauseTime(self, tick):
        self.ticks = int(tick)