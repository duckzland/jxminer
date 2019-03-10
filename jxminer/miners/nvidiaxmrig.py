import re

from miners import Miner
from modules import *
from entities import *

class NvidiaXMRig(Miner):

    """
        Single mining instance for invoking the xmrig nvidia miner
    """

    def init(self):
        self.miner = 'nvidiaxmrig'
        self.setupMiner('gpu')
        allowed = UtilExplode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for xmrig nvidia miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            Logger.printLog('No Nvidia card found, Nvidia XMRig miner only support Nvidia card', 'error')
            self.stop()
            self.shutdown()

        self.setupEnvironment()



    def parse(self, text):
        tmp = UtilStripAnsi(text)
        if 'accepted' in tmp:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"diff \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff ', '')
            except:
                pass

        if 'speed' in tmp:
            try:
                regex = r"15m \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('15m ', '')

            except:
                pass

        return text
