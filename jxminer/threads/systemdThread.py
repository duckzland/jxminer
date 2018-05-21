import os, time
from systemd import journal

from entities.job import *
from thread import Thread
from modules.utility import printLog

class systemdThread(Thread):

    def __init__(self, start):
        self.active = False
        self.job = False
        self.tick = 60
        self.journal = journal.Reader()
        self.trackPhrases = [
            "NVRM: A GPU crash dump has been created. If possible, please run"
        ]
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.tick, self.update)


    def update(self, runner):
        if not self.journal:
            self.journal = journal.Reader()

        self.journal.seek_realtime(time.time() - self.tick)
        for entry in self.journal:
            for testWord in self.trackPhrases:
                if testWord in entry['MESSAGE']:
                    printLog('Rebooting system due to GPU crashed', 'error')
                    os.system('reboot')



    def destroy(self):
        try:
            if not self.journal.closed:
                self.journal.close()

            if self.job:
                self.job.shutdown_flag.set()
        except:
            pass

        finally:
            self.active = False