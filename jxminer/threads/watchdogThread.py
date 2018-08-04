import os, time, re

from entities.job import *
from entities.config import *
from thread import Thread
from modules.utility import printLog, sendSlack

class watchdogThread(Thread):

    def __init__(self, start, Miner):
        self.active = False
        self.job = False
        self.config = Config()
        self.miner = Miner
        self.isRebooting = False
        self.minHashRate = self.miner.wd_hashrate
        self.lastShareCount = False
        self.delay = 60
        self.softRebootCount = 0
        self.loopCount = 0
        self.maxRetry = Config.data.config.watchdog.settings.maximum_retry
        self.boxName = Config.data.config.watchdog.settings.box_name
        self.tick = Config.data.config.watchdog.settings.tick
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.tick, self.update)


    def check(self, newShareCount, newHashRate = False):
        if newShareCount and self.lastShareCount != False and self.lastShareCount == newShareCount:
            self.isRebooting = True
            self.rebootMachine('no share found after %s seconds' % (self.tick))

        elif newHashRate and self.minHashRate != False and float(newHashRate) < float(self.minHashRate):
            self.isRebooting = True
            self.rebootMachine('low hash rate after %s seconds' % (self.tick))

        else:
            self.isRebooting = False
            self.softRebootCount = 0
            self.lastShareCount = newShareCount



    def rebootMachine(self, message):
        countdown = 0
        printLog('Watchdog scheduled to reboot the system in %s seconds due to %s' % (self.delay, message), 'info')
        rebootMessage = 'Watchdog %s is %s rebooting the system due to %s'
        while True:
            countdown += 1
            if countdown == self.delay:
                if self.softRebootCount == self.maxRetry and self.isRebooting:
                    printLog(rebootMessage % (self.boxName, 'hard', message), 'info')
                    sendSlack(rebootMessage % (self.boxName, 'hard', message))
                    time.sleep(3)
                    os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')

                else:
                    self.softRebootCount += 1
                    printLog(rebootMessage % (self.boxName, 'soft', message), 'info')
                    sendSlack(rebootMessage % (self.boxName, 'soft', message))
                    self.miner.reboot()

                self.isRebooting = False
                break




    def update(self, runner):
        if self.loopCount > 0:
            status = self.miner.getStatus()
            shareCount = False
            hashRate = False
            if status and 'shares' in status:
                shareCount = status['shares']

            if status and 'hashrate' in status:
                non_decimal = re.compile(r'[^\d.]+')
                hashRate = non_decimal.sub('', str(status['hashrate']))

            self.check(shareCount, hashRate)

        self.loopCount = 1

