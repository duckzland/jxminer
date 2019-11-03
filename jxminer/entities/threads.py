from entities import Logger

class Threads:

    """
        Class for pooling all thread instances
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
            thread.register(name, self)
            Threads.threads[name] = thread
            Logger.printLog('Started %s' % (name.replace('_', ' ')) , 'success')



    def remove(self, name, thread = False):
        if not thread and self.has(name):
            thread = self.get(name)

        if thread:
            thread.destroy()
            del Threads.threads[name]
            Logger.printLog('Stopped %s' % (name.replace('_', ' ')) , 'success')


    def clean(self):
        for threadName, thread in Threads.threads.items():
            if not thread.isActive():
                self.remove(threadName, thread)


    def destroy(self):
        for threadName, thread in Threads.threads.items():
            self.remove(threadName, thread)



    def start(self):
        for threadName, thread in Threads.threads.items():
            thread.start()
