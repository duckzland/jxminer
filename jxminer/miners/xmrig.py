import sys, re
sys.path.append('../')
from miners.miner import Miner
from modules.utility import stripAnsi

class XMRig(Miner):

    """
        Single mining instance for invoking the xmrig miner
        Currently only supports the CPU miner version
    """

    def init(self):
        self.miner = 'xmrig'
        self.setupMiner('cpu')
        self.checkKeywords = []

        allowed = [
            'cryptonight',
            'cryptonight7',
            'cryptonight7-v1',
            'cryptonight-ipbc',
            'cryptonight-lite',
            'cryptonight-heavy',
            'cryptonight-v1',
            'cryptonight-lite-v1',
            'cryptonight-heavy-v1'
        ]

        if self.algo not in allowed:
            raise ValueError('Invalid coin algo for xmrig cpu miner')


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
