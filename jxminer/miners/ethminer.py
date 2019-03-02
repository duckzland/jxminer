import re

from miners import Miner
from modules import *

class ETHMiner(Miner):

    """
        Single mining instance for invoking the ethminer miner
    """

    def init(self):
        self.miner = 'ethminer'
        self.setupMiner('gpu')
        self.acceptedShares = 0
        self.rejectedShares = 0
        self.checkKeywords = [
            "Error CUDA mining:"
        ]

        amdGPU = self.config.data.dynamic.server.GPU.amd
        nvidiaGPU = self.config.data.dynamic.server.GPU.nvidia

        if self.algo not in ('ethash'):
            raise ValueError('Invalid coin algo for ethminer miner')

        # Nvidia only - use Cuda
        if amdGPU == 0 and nvidiaGPU > 0:
            self.option = self.option + ' #-# ' + self.miner_config.settings.nvidia

        # AMD only - use OpenCL
        elif amdGPU > 0 and nvidiaGPU == 0:
            self.option = self.option + ' #-# ' + self.miner_config.settings.amd

        # Both mode - use both Cuda and OpenCL
        elif amdGPU > 0 and nvidiaGPU > 0:
            self.option = self.option + ' #-# ' + self.miner_config.settings.mixed

        self.setupEnvironment()


    def parse(self, text):
        # Ethminer produces weird ansi color text, remove them all!
        text = stripAnsi(text).encode('ascii', 'ignore')

        # Cleanup text
        try:
            regex = r"(?:cl | m | i | X )"
            m = re.search(regex, text)
            output = m.group(0)
            text = text.replace(output, '')
        except:
            pass

        try:
            regex = r"\d+:\d+:\d+ "
            m = re.search(regex, text)
            output = m.group(0)
            text = text.replace(output, '')
        except:
            pass

        try:
            regex = r"(?:cl-\d+|ethminer|stratum|main) "
            m = re.search(regex, text)
            output = m.group(0)
            text = text.replace(output, '')
        except:
            pass

        text = text.lstrip()

        if 'Speed ' in text:
            try:
                regex = r"Speed \d+.\d+ (?:Mh|H)/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('Speed ', '')

            except:
                pass

        if 'Accepted' in text:
            self.acceptedShares += 1

        if 'Rejected' in text:
            self.rejectedShares += 1

        self.bufferStatus['shares'] = '%s/%s' % (self.acceptedShares, self.rejectedShares)

        return text