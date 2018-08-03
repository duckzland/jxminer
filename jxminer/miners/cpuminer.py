import re

from miners.miner import Miner
from modules.utility import explode

class CpuMiner(Miner):

    """
        Single mining instance for invoking the cpuminer-opt miner and its variation

        Notice
        ======
            cpuminer-opt might not work with old CPU (eg. pentium duo and below), recompilation might be needed
            to support the older generation CPU

        Configuration
        =============
            Configuration file for the miner options and supported algorithm is located at data/miners/cpuminer.ini
    """

    def init(self):
        self.miner = 'cpuminer'
        self.setupMiner('cpu')
        self.checkKeywords = []

        allowed = explode(self.miner_config.default.algo)
        miner_algo = self.algo
        if 'cryptonight' in miner_algo:
            miner_algo = 'cryptonight'

        if miner_algo not in allowed:
            raise ValueError('Invalid coin algo for cpuminer miner')

        self.option = self.option.replace('{cpuminer_algo}', miner_algo)


    def parse(self, text):
        tmp = stripAnsi(text)
        self.bufferStatus['diff'] = ''
        if 'Accepted' in tmp:
            try:
                regex = r"Accepted \d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

        if 'speed' in tmp:
            try:
                regex = r"H, \d+.\d+ (?:MH|H)/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('H, ', '')

            except:
                pass

        return text