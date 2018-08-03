import re

from miners.miner import Miner
from modules.utility import stripAnsi

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

        amdGPU = self.config.data.server.GPU.amd
        nvidiaGPU = self.config.data.server.GPU.nvidia

        if self.algo not in ('ethash'):
            raise ValueError('Invalid coin algo for ethminer miner')

        # Nvidia only - use Cuda
        if amdGPU == 0 and nvidiaGPU > 0:
            self.option = self.option + ' #-# ' + self.miner_config.default.nvidia

        # AMD only - use OpenCL
        elif amdGPU > 0 and nvidiaGPU == 0:
            self.option = self.option + ' #-# ' + self.miner_config.default.amd

        # Both mode - use both Cuda and OpenCL
        elif amdGPU > 0 and nvidiaGPU > 0:
            self.option = self.option + ' #-# ' + self.miner_config.default.mixed

        self.setupEnvironment()


    def parse(self, text):
        # Ethminer produces weird ansi color text, remove them all!
        text = stripAnsi(text).encode('ascii', 'ignore')

        if 'Speed:' in text:
            try:
                regex = r" [A\d++\d+:R\d++\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace(' [A', '').replace(':', '/').replace('R', '')
            except:
                pass

            try:
                regex = r"\d+.\d+ (?:Mh|H)/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output

            except:
                pass

        return text