import sys
sys.path.append('../')
from miners.miner import Miner

class Claymore(Miner):

    """
        Single mining instance for invoking the claymore miner and its variation
    """

    def init(self):
        self.miner = 'claymore'
        self.setupMiner('gpu')
        self.checkKeywords = [
            "need to restart miner"
        ]

        if self.algo not in ('ethash', 'equihash', 'cryptonight7', 'cryptonight'):
            raise ValueError('Invalid coin algo for claymore miner')

        if hasattr(self, 'second_algo') and self.second_algo not in ('blake2s'):
            raise ValueError('Invalid secondary coin algo for claymore dual miner')

        if self.algo in ('equihash', 'cryptonight', 'crytonight7') and self.config['server'].getint('GPU', 'amd') == 0:
            raise ValueError('No AMD card found, Claymore miner for % does\'t only support AMD card' % (self.algo))

        if self.coin not in 'eth':
            self.option = (
                self.option
                    .replace('{allcoins}', '1')
                    .replace('{nofee}', '1')
            )
        else:
            self.option = (
                self.option
                    .replace('{allcoins}', '0')
                    .replace('{nofee}', '0')
            )

        #self.setupEnvironment()
