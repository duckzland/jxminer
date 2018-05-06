import sys
sys.path.append('../')
from miners.miner import Miner

class EWBF(Miner):

    """
        Single mining instance for invoking the ewbf miner
    """

    def init(self):
        self.miner = 'ewbf'
        self.setupMiner('gpu')

        if self.algo not in ('equihash'):
            raise ValueError('Invalid coin algo for ewbf miner')

        if self.config['server'].getint('GPU', 'nvidia') == 0:
            raise ValueError('No Nvidia card,  ewbf miner only support Nvidia card')


        #self.setupEnvironment()
