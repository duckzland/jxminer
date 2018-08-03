import re

from miners.miner import Miner
from modules.utility import stripAnsi

class NvidiaXMRig(Miner):

    """
        Single mining instance for invoking the xmrig nvidia miner
    """

    def init(self):
        self.miner = 'nvidiaxmrig'
        self.setupMiner('gpu')
        self.checkKeywords = []

        allowed = [
            'cryptonight',
            'cryptonight7',
            'cryptonight7-v3',
            'cryptonight7-v4',
            'cryptonight7-v8',
            'cryptonight-ipbc',
            'cryptonight-lite',
            'cryptonight-heavy',
            'cryptonight-v1',
            'cryptonight-lite-v1',
            'cryptonight-heavy-v1'
        ]

        if self.algo not in allowed:
            raise ValueError('Invalid coin algo for xmrig nvidia miner')

        if self.config.data.server.GPU.nvidia == 0:
            raise ValueError('No AMD card found, Nvidia XMRig miner only support Nvidia card')

        self.setupEnvironment()



    def parse(self, text):
        tmp = stripAnsi(text)
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
