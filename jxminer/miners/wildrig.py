import re

from miners import Miner
from modules import *
from entities import *

class WildRig(Miner):

    """
        Single mining instance for invoking the wildrig miner
    """

    def init(self):
        self.miner = 'wildrig'
        self.setupMiner('gpu')
        self.acceptedShares = 0
        self.rejectedShares = 0

        allowed = UtilExplode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for wildrig miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.amd == 0:
            Logger.printLog('No AMD card found, WildRig only supports amd card', 'error')
            self.stop()
            self.shutdown()

        self.option = self.option.replace('{wildrig_algo}', self.algo)
        self.setupEnvironment()



    def parse(self, text):

        ## Shorten the text ##
        regex = r"\[\d+:\d+:\d+\] "
        m = re.search(regex, text)
        output = m.group(0)
        text = text.replace(output, '')
        tmp = UtilStripAnsi(text);

        if 'accepted' in tmp:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output

            except:
                pass

        if 'speed ' in tmp:
            try:
                regex = r"\d+ (m|k)H\/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output

            except:
                pass

        if 'diff ' in tmp:
            try:
                regex = r"diff \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff ', '')
            except:
                pass

        return text