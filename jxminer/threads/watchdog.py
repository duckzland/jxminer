import os, time, re

from threads import Thread
from entities import *
from modules import *
from pprint import pprint

class watchdog(Thread):

    def __init__(self, **kwargs):
        super(watchdog, self).__init__()
        self.setPauseTime(1)
        self.configure(**kwargs)


    def init(self):
        self.miner = self.args.get('miner', False)
        self.threads = self.args.get('threads', False)
        self.isRebooting = False
        self.lastShareCount = False
        self.readyToBoot = False
        self.softRebootCount = 0
        self.minHashRate = self.miner.wd_hashrate
        self.delay = Config.data.config.watchdog.settings.delay
        self.reboot_delay = Config.data.config.watchdog.settings.reboot_delay
        self.maxRetry = Config.data.config.watchdog.settings.maximum_retry
        self.boxName = Config.data.config.machine.settings.box_name

        self.setPauseTime(Config.data.config.watchdog.settings.tick)

        if self.args.get('start', False):
            self.start()



    def update(self):

        if not self.readyToBoot:
            for i in range(int(self.delay)):
                time.sleep(1)
            self.readyToBoot = True
            Logger.printLog('Watchdog is monitoring', 'info')

        if not self.isRebooting:
            status = self.miner.getStatus()
            shareCount = False
            hashRate = False

            if status and 'shares' in status:
                tails = re.compile(r"/\d+")
                shareCount = tails.sub('', str(status['shares']))

            if status and 'hashrate' in status:
                non_decimal = re.compile(r'[^\d.]+')
                hashRate = non_decimal.sub('', str(status['hashrate']))

            self.check(shareCount, hashRate)



    def destroy(self):
        self.stop()
        Logger.printLog("Stopping watchdog manager", 'success')



    def check(self, newShareCount = False, newHashRate = False):
        if newShareCount and self.lastShareCount != False and int(self.lastShareCount) == int(newShareCount):
            self.isRebooting = True
            self.rebootMachine('no share found after %s seconds interval' % (self.tick))

        elif newHashRate and self.minHashRate != False and float(newHashRate) < float(self.minHashRate):
            self.isRebooting = True
            self.rebootMachine('low hash rate after %s seconds interval' % (self.tick))

        else:
            Logger.printLog('Watchdog reporting miner is healthy', 'success')
            self.lastShareCount = newShareCount



    def rebootMachine(self, message):
        Logger.printLog('Watchdog scheduled to reboot the system in %s seconds due to %s' % (self.reboot_delay, message), 'info')
        rebootMessage = 'Watchdog %s is %s rebooting the system due to %s'
        rebootDelay = int(self.reboot_delay) - 1

        for i in range(int(self.reboot_delay)):

            time.sleep(1)
            Logger.printLog('%s/%s Rebooting countdown - press ctrl+c to cancel' % (i, rebootDelay))

            if int(i) == rebootDelay:
                if int(self.softRebootCount) > int(self.maxRetry) and self.isRebooting:
                    Logger.printLog(rebootMessage % (self.boxName, 'hard', message), 'info')
                    UtilSendSlack(rebootMessage % (self.boxName, 'hard', message))
                    time.sleep(3)
                    try:
                        os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')
                    except:
                        os.system("reboot -f")

                else:
                    self.softRebootCount += 1
                    Logger.printLog(rebootMessage % (self.boxName, 'soft', message), 'info')
                    UtilSendSlack(rebootMessage % (self.boxName, 'soft', message))

                    self.isRebooting = False
                    self.lastShareCount = False
                    self.readyToBoot = False

                    self.miner.stop()

                    time.sleep(10)
                    self.miner.start()
