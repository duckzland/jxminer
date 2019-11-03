from threads import Thread
from entities import *
from miners import *


class cpuMiner(Thread, threading.Thread):

    def __init__(self, **kwargs):
        super(cpuMiner, self).__init__()
        self.setPauseTime(1)
        self.configure(**kwargs)


    def init(self):
        self.selectMiner()
        if self.args.get('start', False):
            self.start()


    def update(self):
        if self.isActive():
            self.miner.start()
        else:
            if self.miner.check() == 'give_up':
                self.destroy()


    def destroy(self):
        if self.isActive():
            self.miner.shutdown()
            self.stop()

        Logger.printLog("Stopping cpu miner manager", 'success')


    def selectMiner(self):
        return
        c = self.config.data.config
        coin = c.machine.cpu_miner.coin
        algo = c.coins[coin].algo
        miner = c.miner[algo].cpu

        if miner in 'cpuminer':
            self.config.load('miners', 'cpuminer.ini', True)
            self.miner = CpuMiner()

        elif miner in 'cpuxmrig':
            self.config.load('miners', 'cpuxmrig.ini', True)
            self.miner = CpuXMRig()

        else:
            Logger.printLog('Refused to load invalid miner program type', 'error')
            self.destroy()
