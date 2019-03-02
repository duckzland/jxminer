from threads import Thread
from entities import *
from miners import *

class cpuMiner(Thread):

    def __init__(self, start):
        self.active = False
        self.job = False
        self.config = Config()
        self.miner = False
        self.started = False
        self.exiting = False
        if start:
            self.start()


    def init(self):
        self.job = Job(1, self.update)


    def start(self):
        try:
            self.selectMiner()
            self.init()
            self.job.start()
        except:
            self.active = False

        finally:
            self.active = True


    def update(self, runner):
        if not self.exiting:
            if not self.started:
                self.miner.start()
                self.started = True
            else:
                if self.miner.check() == 'give_up':
                    self.exiting = True
                    self.destroy()


    def destroy(self):
        self.exiting = True
        if self.job:
            self.miner.shutdown()
            self.job.shutdown_flag.set()

        self.started = False
        Logger.printLog("Stopping cpu miner manager", 'success')


    def selectMiner(self):
        c = self.config.data.config
        coin = c.machine.cpu_miner.coin
        algo = c.coins[coin].algo
        miner = c.miner[algo].cpu

        if miner in 'cpuminer':
            #self.config.load('miners', 'cpuminer.ini', True)
            self.miner = CpuMiner()

        elif miner in 'cpuxmrig':
            #self.config.load('miners', 'cpuxmrig.ini', True)
            self.miner = CpuXMRig()

        else:
            Logger.printLog('Refused to load invalid miner program type', 'error')
            self.destroy()