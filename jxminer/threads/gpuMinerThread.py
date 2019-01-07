from thread import Thread
from entities.job import *
from entities.config import *

from miners.ccminer import *
from miners.claymore import *
from miners.ethminer import *
from miners.ewbf import *
from miners.miner import *
from miners.sgminer import *
from miners.amdxmrig import *
from miners.nvidiaxmrig import *
from miners.castxmr import *
from miners.cryptodredge import *
from miners.phoenixminer import *

from entities.logger import *

class gpuMinerThread(Thread):

    def __init__(self, start):
        self.active = False
        self.job = False
        self.config = Config()
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
        self.exiting = True
        if self.job:
            for miner in self.miners:
                miner.shutdown()
            self.job.shutdown_flag.set()

        self.started = False
        Logger.printLog("Stopping gpu miner manager", 'success')



    def selectMiner(self):
        c         = self.config.data.config
        d         = self.config.data.dynamic
        coin      = c.machine.gpu_miner.coin
        algo      = c.coins[coin].algo
        doDual    = c.machine.gpu_miner.dual
        amd       = c.miner[algo].amd
        nvidia    = c.miner[algo].nvidia
        dual      = c.miner[algo].dual
        amdGPU    = d.server.GPU.amd
        nvidiaGPU = d.server.GPU.nvidia
        miners = []

        # AMD miner
        if amdGPU > 0 and amd:
            miners.append(amd)

        # Nvidia miner
        if nvidiaGPU > 0 and nvidia and nvidia not in miners:
            miners.append(nvidia)

        # Dual Miner
        if doDual and dual and dual not in miners:
            miners.append(dual)

        for miner in miners:
            if miner in 'ccminer':
                self.config.load('miners', 'ccminer.ini', True)
                self.miners.append(CCMiner())

            elif miner in 'claymore':
                self.config.load('miners', 'claymore.ini', True)
                self.miners.append(Claymore())

            elif miner in 'ethminer':
                self.config.load('miners', 'ethminer.ini', True)
                self.miners.append(ETHMiner())

            elif miner in 'ewbf':
                self.config.load('miners', 'ewbf.ini', True)
                self.miners.append(EWBF())

            elif miner in 'sgminer':
                self.config.load('miners', 'sgminer.ini', True)
                self.miners.append(SGMiner())

            elif miner in 'amdxmrig':
                self.config.load('miners', 'amdxmrig.ini', True)
                self.miners.append(AmdXMRig())

            elif miner in 'nvidiaxmrig':
                self.config.load('miners', 'nvidiaxmrig.ini', True)
                self.miners.append(NvidiaXMRig())

            elif miner in 'castxmr':
                self.config.load('miners', 'castxmr.ini', True)
                self.miners.append(CastXmr())

            elif miner in 'cryptodredge':
                self.config.load('miners', 'cryptodredge.ini', True)
                self.miners.append(CryptoDredge())

            elif miner in 'phoenixminer':
                self.config.load('miners', 'phoenixminer.ini', True)
                self.miners.append(PhoenixMiner())

            else:
                Logger.printLog('Refused to load invalid miner program type', 'error')