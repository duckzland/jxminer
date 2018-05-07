import sys, re
sys.path.append('../')
from miners.miner import Miner
from modules.utility import explode

class CpuMiner(Miner):

    """
        Single mining instance for invoking the cpuminer-opt miner and its variation
    """

    def init(self):
        self.miner = 'cpuminer'
        self.setupMiner('cpu')
        self.checkKeywords = []

        allowed = explode(self.miner_config.get('default', 'algo'))
        miner_algo = self.algo
        if 'cryptonight' in miner_algo:
            miner_algo = 'cryptonight'

        if miner_algo not in allowed:
            raise ValueError('Invalid coin algo for cpuminer miner')

        self.option = self.option.replace('{cpuminer_algo}', miner_algo)
        print self.option
