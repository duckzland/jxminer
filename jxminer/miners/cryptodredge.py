import re
from miners import Miner
from modules import *
from entities import *

class CryptoDredge(Miner):

    """
        Single mining instance for invoking the cryptodredge miner
    """

    def init(self):

        self.miner = 'cryptodredge'
        self.setupMiner('gpu')
        allowed = UtilExplode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for CryptoDredge miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            Logger.printLog('No Nvidia card found, CryptoDredge only supports Nvidia card', 'error')
            self.stop()
            self.shutdown()

        self.option = self.option.replace('{cryptodredge_algo}', self.algo)
        self.setupEnvironment()




    def parse(self, text):

        ## Shorten the text ##
        regex = r"\[\d+:\d+:\d+\] "
        m = re.search(regex, text)
        output = m.group(0)
        text = text.replace(output, '')
        tmp = UtilStripAnsi(text)

        if 'Accepted : ' in tmp:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"diff=\d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff=', '')
            except:
                pass

            try:
                regex = r": \d+.\d+(M|K)H\/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace(': ', '')

            except:
                pass

        return text