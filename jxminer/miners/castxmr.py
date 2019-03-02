import re
from miners import Miner
from modules import *

class CastXmr(Miner):

    """
        Single mining instance for invoking the castxmr
    """

    def init(self):

        self.miner = 'castxmr'
        self.setupMiner('gpu')
        self.checkKeywords = []

        allowed = explode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            raise ValueError('Invalid coin algo for CastXMR miner')

        if self.config.data.dynamic.server.GPU.amd == 0:
            raise ValueError('No AMD card found, CastXMR only supports AMD card')

        gpuNumber = ','.join(map(str, range(0, self.config.data.dynamic.server.GPU.amd)))

        self.option = self.option.replace('{castxmr_gpu}', gpuNumber)
        self.setupEnvironment()




    def parse(self, text):
        if 'Shares:' in text:
            try:
                regex = r"Shares: \d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('Shares: ', '')
            except:
                pass

            try:
                regex = r"Hash Rate Avg: \d+.\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff ', '')
            except:
                pass

            try:
                regex = r", \d+.\d+( M| k| )H"
                regex = r"Hash Rate Avg: \d+.\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('Hash Rate Avg: ', '')

            except:
                pass


        if 'Difficulty changed. Now: ' in text:
            self.bufferStatus['diff'] = text.replace('Difficulty changed. Now: ', '')

        return text