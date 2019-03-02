import re

from miners import Miner
from modules import *

class SGMiner(Miner):

    """
        Single mining instance for invoking the sgminer-gm
    """

    def init(self):
        self.miner = 'sgminer'
        self.setupMiner('gpu')

        allowed = explode(self.miner_config.settings.algo)

        miner_algo = self.algo
        if 'cryptonight' in miner_algo:
            miner_algo = 'cryptonight'

        if miner_algo not in allowed:
            raise ValueError('Invalid coin algo for sgminer miner')

        if self.config.data.dynamic.server.GPU.amd == 0:
            raise ValueError('No AMD card found, SGMiner only supports amd card')

        self.option = self.option.replace('{sgminer_algo}', miner_algo)

        self.setupEnvironment()


    def parse(self, text):

        ## Shorten the text ##
        try:
            regex = r"\[\d+:\d+:\d+\] "
            m = re.search(regex, text)
        except:
            pass

        output = m.group(0)
        text = text.replace(output, '')

        if 'avg' in text:
            try:
                regex = r"A:\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('A:', '')
            except:
                pass

            try:
                regex = r"\(avg\):\d+.\d+(M|K)h\/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('(avg):', '')

            except:
                pass

        if ' Diff ' in text:
            try:
                regex = r"Diff \d+.\d+/\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('Diff ', '')
            except:
                pass

        return text
