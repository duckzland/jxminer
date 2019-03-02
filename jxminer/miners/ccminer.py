import re
from miners import Miner
from modules import *

class CCMiner(Miner):

    """
        Single mining instance for invoking the ccminer and its variation
    """

    def init(self):

        self.miner = 'ccminer'
        self.setupMiner('gpu')
        self.checkKeywords = [
            "watchdog: BUG: soft lockup",
            "Cuda error",
            "illegal memory",
        ]

        allowed = explode(self.miner_config.settings.algo)

        miner_algo = self.algo

        if 'cryptonight' in miner_algo:
            miner_algo = 'cryptonight'

        if 'cryptonight7' in miner_algo:
            miner_algo = 'monero'

        if miner_algo not in allowed:
            raise ValueError('Invalid coin algo for ccminer miner')

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            raise ValueError('No Nvidia card found, CCMiner only supports Nvidia card')

        self.option = self.option.replace('{ccminer_algo}', miner_algo)
        self.setupEnvironment()




    def parse(self, text):
        if 'accepted:' in text:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"diff \d+.\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff ', '')
            except:
                pass

            try:
                regex = r", \d+.\d+( M| k| )H"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace(', ', '')

            except:
                pass

        return text