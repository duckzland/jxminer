import os, time
from modules.utility import printLog, sendSlack

class WatchDog:

    """
        This is a class for detecting low hashrate
    """

    def __init__(self, Config):
        self.config = Config
        self.isRebooting = False
        self.lastHashRate = 0
        self.delay = 60


    def check(self, newHashRate):
        if self.lastHashRate == newHasRate:
            self.isRebooting = True
            self.rebootMachine()

        else:
            self.isRebooting = False


    def rebootMachine(self):
        time.sleep(self.delay)
        if self.isRebooting:
            printLog('Rebooting system in %seconds' % (self.delay), 'error')
            sendSlack('Watchdog %s is rebooting the system due to low hashrate' % (self.config['machine'].get('settings', 'box_name')))
            os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')
