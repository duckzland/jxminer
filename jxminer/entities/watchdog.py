import os, time
from modules.utility import printLog, sendSlack

class WatchDog:

    """
        This is a class for detecting low hashrate
    """

    def __init__(self, Config):
        self.config = Config
        self.isRebooting = False
        self.lastHashRate = False
        self.delay = 60


    def check(self, newHashRate):
        if self.lastHashRate == newHashRate:
            self.isRebooting = True
            self.rebootMachine()

        else:
            self.isRebooting = False
            self.lastHashRate = newHashRate


    def rebootMachine(self):

        printLog('Watchdog scheduled to reboot the system in %s seconds due to low hashrate detected' % (self.delay), 'info')
        time.sleep(self.delay)

        if self.isRebooting:
            sendSlack('Watchdog %s is rebooting the system due to low hashrate' % (self.config['machine'].get('settings', 'box_name')))
            os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')
