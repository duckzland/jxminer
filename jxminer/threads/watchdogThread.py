import os, time, re

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
        self.minHashRate = Config['watchdog'].get('settings', 'minimum_hashrate')
        self.lastShareCount = False
        self.delay = 60
        self.softRebootCount = 0
        self.maxRetry = Config['watchdog'].getint('settings', 'maximum_retry')
        self.boxName = Config['machine'].get('settings', 'box_name')
        self.tick = Config['watchdog'].getint('settings', 'tick')
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.tick, self.update)


    def check(self, newShareCount, newHashRate = False):
        if newShareCount and self.lastShareCount != False and self.lastShareCount == newShareCount:
            self.isRebooting = True
            self.rebootMachine('no share found after %s seconds' % (self.tick))

        elif newHashRate and self.minHashRate != False and int(newHashRate) < int(self.minHashRate):
            self.isRebooting = True
            self.rebootMachine('low hash rate after %s seconds' % (self.tick))

        else:
            self.isRebooting = False
            self.softRebootCount = 0
            self.lastShareCount = newShareCount



    def rebootMachine(self, message):
        printLog('Watchdog scheduled to reboot the system in %s seconds due to %s' % (self.delay, message), 'info')
        countdown = 0
        while True:
            countdown += 1
            if countdown == self.delay and self.isRebooting:
                if self.softRebootCount == self.maxRetry:
                    sendSlack('Watchdog %s is hard rebooting the system due to %s' % (self.boxName, message))
                    time.sleep(3)
                    os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')
                else:
                    self.softRebootCount += 1
                    sendSlack('Watchdog %s is soft rebooting the miner due to %s' % (self.boxName, message))
                    self.miner.reboot()



    def update(self, runner):
        status = self.miner.getStatus()
        shareCount = False
        hashRate = False
        if status and 'shares' in status:
            shareCount = status['shares']

        if status and 'hashrate' in status:
            non_decimal = re.compile(r'[^\d.]+')
            hashRate = non_decimal.sub('', status['hashrate'])

        self.check(shareCount, hashRate)

