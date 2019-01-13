import re, os
from miners.miner import Miner

class PhoenixMiner(Miner):

    """
        Single mining instance for invoking the phonix miner
    """

    def init(self):
        self.miner = 'phoenixminer'
        self.setupMiner('gpu')
        self.checkKeywords = [
            'CUDART error',
            'Allocating buffers failed with'
        ]

        if self.algo not in ('ethash'):
            raise ValueError('Invalid coin algo for phoenix miner')

        self.setupEnvironment()


    def parse(self, text):
        self.bufferStatus['diff'] = 'N/A'
        if ' speed: ' in text:
            try:
                regex = r"shares: \d+/\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('shares: ', '')
            except:
                pass

            try:
                regex = r"speed: \d+.\d*|\d* (?:MH|H)/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('speed: ', '')

            except:
                pass

        return text