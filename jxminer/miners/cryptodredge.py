import re
from miners import Miner
from modules import *

class CryptoDredge(Miner):

    """
        Single mining instance for invoking the cryptodredge miner
    """

    def init(self):

        self.miner = 'cryptodredge'
        self.setupMiner('gpu')
        self.checkKeywords = []

        allowed = explode(self.miner_config.settings.algo)

        miner_algo = self.algo

        if 'cryptonight7' in miner_algo:
            miner_algo = 'cnv7'

        if 'cryptonight-heavy' in miner_algo:
            miner_algo = 'cnheavy'

        if miner_algo == 'cryptonight7-v8':
            miner_algo = 'cnv8'

        if miner_algo == 'cryptonight-haven':
            miner_algo = 'cnhaven'

        if miner_algo == 'cryptonight-fast':
            miner_algo = 'cnfast'

        if miner_algo not in allowed:
            raise ValueError('Invalid coin algo for CryptoDredge miner')

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            raise ValueError('No Nvidia card found, CryptoDredge only supports Nvidia card')

        self.option = self.option.replace('{cryptodredge_algo}', miner_algo)
        self.setupEnvironment()




    def parse(self, text):

        ## Shorten the text ##
        regex = r"\[\d+:\d+:\d+\] "
        m = re.search(regex, text)
        output = m.group(0)
        text = text.replace(output, '')

        if 'Accepted : ' in text:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"diff=\d+.\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff=', '')
            except:
                pass

            try:
                regex = r": \d+.\d+(M|K)H\/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace(': ', '')

            except:
                pass

        return text