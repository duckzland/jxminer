import sys
from thread import Thread
sys.path.append('../')
from entities.job import *

from miners.cpuminer import *
from miners.xmrig import *

from modules.utility import printLog

class MonitorCPUMiner(Thread):

    def __init__(self, start, Config):
        self.active = False
        self.job = False
        self.config = Config
        self.miner = False
        self.started = False
        self.exiting = False
        self.selectMiner()
        self.init()
        if start:
            self.start()


    def init(self):
        self.job = Job(1, self.update)


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
        try:
            self.exiting = True
            if self.job:
                self.miner.shutdown()
                self.job.shutdown_flag.set()

            self.started = False
            status = 'success'
        except:
            status = 'error'
        finally:
            printLog("Stopping cpu miner manager", status)


    def selectMiner(self):
        coin = self.config['machine'].get('cpu_miner', 'coin')
        algo = self.config['coins'].get(coin, 'algo')
        miner = self.config['miner'].get(algo, 'cpu')
        if miner in 'cpuminer':
            self.miner = CpuMiner(self.config)

        elif miner in 'xmrig':
            self.miner = XMRig(self.config)

        else:
            raise ValueError('Refused to load invalid miner program type')