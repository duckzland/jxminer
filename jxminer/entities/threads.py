from modules.utility import sendSlack
from entities.logger import *

class Threads:

    """
        Class for pooling all thread instance
    """

    threads = dict()

    def __init__(self):
        Threads.threads = dict()


    def extract(self):
        return Threads.threads


    def has(self, name):
        return name in Threads.threads


    def get(self, name):
        return Threads.threads[name]


    def process(self, name, thread, action):
        if action is True:
            self.add(name, thread)
        else:
            self.remove(name)


    def add(self, name, thread):
        if not self.has(name):
            try:
                thread.register(name, self)
                Threads.threads[name] = thread
                status = 'success'

            except:
                status = 'error'

            finally:
                Logger.printLog('Starting %s manager' % (name.replace('_', ' ')) , status)



    def remove(self, name, thread = False):
        if not thread:
            if self.has(name):
                thread = self.get(name)

        if thread:
            try:
                thread.destroy()
                del Threads.threads[name]
                status='success'

            except:
                status = 'error'

            finally:
                Logger.printLog('Stopping %s manager' % (name.replace('_', ' ')) , status)


    def clean(self):
        for threadName, thread in Threads.threads.items():
            if not thread.active:
                self.remove(threadName, thread)

    def destroy(self):
        for threadName, thread in Threads.threads.items():
            self.remove(threadName, thread)


    def start(self):
        for threadName, thread in Threads.threads.items():
            thread.start()

