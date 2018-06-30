import signal

class Shutdown():

    """
    Catching shutdown signal
    """

    isShuttingDown = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum, frame):
        self.isShuttingDown = True