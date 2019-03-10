import re, os
from miners import Miner
from modules import *
from entities import *

class TeamRedMiner(Miner):

    """
        Single mining instance for invoking the teamredminer
    """

    def init(self):
        self.miner = 'teamredminer'
        self.setupMiner('gpu')
        allowed = UtilExplode(self.miner_config.settings.algo)
        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for teamredminer miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.amd == 0:
            Logger.printLog('No AMD card found, TeamRedMiner only supports amd card', 'error')
            self.stop()
            self.shutdown()

        self.option = self.option.replace('{teamredminer_algo}', self.algo)
        self.setupEnvironment()


    def parse(self, text):
        self.bufferStatus['diff'] = 'N/A'
        keyword = ' Total '
        if self.config.data.dynamic.server.GPU.amd == 1:
            keyword = ' GPU 0 '

        tmp = UtilStripAnsi(text)
        if keyword in tmp:
            try:
                regex = r" a:\d+ r:\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace(' a:', '').replace(' r:', '/')
            except:
                pass

            try:
                regex = r" avg \d+.\d+(?:mh|kh| h)/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace(' avg ', '')

            except:
                pass

        return text