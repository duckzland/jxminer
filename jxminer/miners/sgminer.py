import re

from miners.miner import Miner
from modules.utility import explode

class SGMiner(Miner):

    """
        Single mining instance for invoking the sgminer-gm
    """

    def init(self):
        self.miner = 'sgminer'
        self.setupMiner('gpu')

        allowed = explode(self.miner_config.get('default', 'algo'))
        miner_algo = self.algo
        if 'cryptonight' in miner_algo:
            miner_algo = 'cryptonight'

        if miner_algo not in allowed:
            raise ValueError('Invalid coin algo for sgminer miner')

        if self.config.data.dynamic.server.GPU.amd == 0:
            raise ValueError('No AMD card found, SGMiner only supports amd card')

        self.option = self.option.replace('{sgminer_algo}', miner_algo)

        self.setupEnvironment()
