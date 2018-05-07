import sys, re
sys.path.append('../')
from miners.miner import Miner
from modules.utility import explode

class ETHMiner(Miner):

    """
        Single mining instance for invoking the ethminer miner
    """

    def init(self):
        self.miner = 'ethminer'
        self.setupMiner('gpu')
        self.checkKeywords = [
            "Error CUDA mining:"
        ]

        amdGPU = self.config['server'].getint('GPU', 'amd')
        nvidiaGPU = self.config['server'].getint('GPU', 'nvidia')

        if self.algo not in ('ethash'):
            raise ValueError('Invalid coin algo for ethminer miner')

        # Nvidia only - use Cuda
        if amdGPU == 0 and nvidiaGPU > 0:
            self.option = self.option + self.miner_config.get('default', 'nvidia')

        # AMD only - use OpenCL
        elif amdGPU > 0 and nvidiaGPU == 0:
            self.option = self.option + self.miner_config.get('default', 'amd')

        # Both mode - use both Cuda and OpenCL
        elif amdGPU > 0 and nvidiaGPU > 0:
            self.option = self.option + self.miner_config.get('default', 'mixed')

        self.setupEnvironment()