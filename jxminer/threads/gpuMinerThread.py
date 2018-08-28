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
            Logger.printLog("Stopping gpu miner manager", status)



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

            else:
                Logger.printLog('Refused to load invalid miner program type', 'error')