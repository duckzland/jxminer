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


    def add(self, name, thread):
        if name not in Threads.threads:
            thread.register(name, self)
            Threads.threads[name] = thread


    def remove(self, name):
        for threadName, thread in Threads.threads.items():
            if name in threadName:
                thread.destroy()
                del Threads.threads[threadName]


    def clean(self):
        for threadName, thread in Threads.threads.items():
            if not thread.active:
                thread.destroy()
                del Threads.threads[threadName]


    def destroy(self):
        for threadName, thread in Threads.threads.items():
            thread.destroy()
            del Threads.threads[threadName]

