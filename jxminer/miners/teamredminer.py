import re, os
from miners import Miner
from modules import *

class TeamRedMiner(Miner):

    """
        Single mining instance for invoking the teamredminer
    """

    def init(self):
        self.miner = 'teamredminer'
        self.setupMiner('gpu')
        self.checkKeywords = [
        ]

        allowed = explode(self.miner_config.settings.algo)
        if self.algo not in allowed:
            raise ValueError('Invalid coin algo for teamredminer miner')

        if self.algo == 'cryptonight7':
            self.algo = 'cnv8'

        if self.config.data.dynamic.server.GPU.amd == 0:
            raise ValueError('No AMD card found, TeamRedMiner only supports amd card')

        self.option = self.option.replace('{teamredminer_algo}', self.algo)

        self.setupEnvironment()


    def parse(self, text):
        self.bufferStatus['diff'] = 'N/A'
        keyword = ' Total '
        if self.config.data.dynamic.server.GPU.amd == 1:
            keyword = ' GPU 0 '

        if keyword in text:
            try:
                regex = r" a:\d+ r:\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace(' a:', '').replace(' r:', '/')
            except:
                pass

            try:
                regex = r" avg \d+.\d+(?:mh|kh| h)/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace(' avg ', '')

            except:
                pass

        return text