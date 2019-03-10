import re
from miners import Miner
from modules import *
from entities import *

class CCMiner(Miner):

    """
        Single mining instance for invoking the ccminer and its variation
    """

    def init(self):

        self.miner = 'ccminer'
        self.setupMiner('gpu')

        allowed = UtilExplode(self.miner_config.settings.algo)
        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for ccminer miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            Logger.printLog('No Nvidia card found, CCMiner only supports Nvidia card', 'error')
            self.stop()
            self.shutdown()

        self.option = self.option.replace('{ccminer_algo}', self.algo)
        self.setupEnvironment()




    def parse(self, text):
        tmp = UtilStripAnsi(text)
        if 'accepted:' in tmp:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"diff \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff ', '')
            except:
                pass

            try:
                regex = r", \d+.\d+( M| k| )H"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace(', ', '')

            except:
                pass

        return text