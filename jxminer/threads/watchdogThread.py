import os, time

from entities.job import *
from thread import Thread
from modules.utility import printLog, sendSlack

class watchdogThread(Thread):

    def __init__(self, start, Config, Miner):
        self.active = False
        self.job = False
        self.config = Config
        self.miner = Miner
        self.isRebooting = False
        self.lastHashRate = False
        self.delay = 60
        self.softRebootCount = 0
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config['watchdog'].getint('settings', 'tick'), self.update)


    def check(self, newHashRate):
        if self.lastHashRate == newHashRate and self.lastHashRate != False:
            self.isRebooting = True
            if self.softRebootCount == Config['watchdog'].getint('settings', 'maximum_retry'):
                self.rebootMachine()
            else:
                self.softRebootCount += 1
                self.miner.reboot()

        else:
            self.isRebooting = False
            self.softRebootCount = 0
            self.lastHashRate = newHashRate


    def rebootMachine(self):
        printLog('Watchdog scheduled to reboot the system in %s seconds due to low hashrate detected' % (self.delay), 'info')
        countdown = 0
        while True:
            countdown += 1
            if countdown == self.delay and self.isRebooting:
                sendSlack('Watchdog %s is rebooting the system due to low hashrate' % (self.config['machine'].get('settings', 'box_name')))
                time.sleep(3)
                os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')


    def update(self, runner):
        status = self.miner.getStatus()
        if status and 'shares' in status:
            self.check(status['shares'])

