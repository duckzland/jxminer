import sys
from thread import Thread
sys.path.append('../')
from entities.job import *

from miners.ccminer import *
from miners.claymore import *
from miners.ethminer import *
from miners.ewbf import *
from miners.miner import *
from miners.sgminer import *

from modules.utility import printLog

class MonitorGPUMiner(Thread):

    def __init__(self, start, Config):
        self.active = False
        self.job = False
        self.config = Config
        self.miners = []
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
                for miner in self.miners:
                    miner.start()
                self.started = True
            else:
                for miner in self.miners:
                    if miner.check() == 'give_up':
                        self.exiting = True
                        self.destroy()
                        break


    def destroy(self):
        try:
            self.exiting = True
            if self.job:
                for miner in self.miners:
                    miner.shutdown()
                self.job.shutdown_flag.set()

            self.started = False
            status = 'success'

        except:
            status = 'error'

        finally:
            printLog("Stopping gpu miner manager", status)



    def selectMiner(self):
        coin = self.config['machine'].get('gpu_miner', 'coin')
        algo = self.config['coins'].get(coin, 'algo')
        doDual = self.config['machine'].getboolean('gpu_miner', 'dual')
        amd = self.config['miner'].get(algo, 'amd')
        nvidia = self.config['miner'].get(algo, 'nvidia')
        dual = self.config['miner'].get(algo, 'dual')
        amdGPU = self.config['server'].getint('GPU', 'amd')
        nvidiaGPU = self.config['server'].getint('GPU', 'nvidia')
        miners = []

        if doDual and dual:
            miners.append(dual)
        else:
            # Nvidia only
            if amdGPU == 0 and nvidiaGPU > 0 and nvidia:
                miners.append(nvidia)

            # AMD only
            elif amdGPU > 0 and nvidiaGPU == 0 and amd:
                miners.append(amd)

            # Mixed mode
            elif amdGPU > 0 and nvidiaGPU > 0 and nvidia and amd:
                if amd == nvidia:
                    miners.append(amd)
                else:
                    miners.append(amd)
                    miners.append(nvidia)

        for miner in miners:
            if miner in 'ccminer':
                self.miners.append(CCMiner(self.config))

            elif miner in 'claymore':
                self.miners.append(Claymore(self.config))

            elif miner in 'ethminer':
                self.miners.append(ETHMiner(self.config))

            elif miner in 'ewbf':
                self.miners.append(EWBF(self.config))

            elif miner in 'sgminer':
                self.miners.append(SGMiner(self.config))

            else:
                raise ValueError('Refused to load invalid miner program type')

