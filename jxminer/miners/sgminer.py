import re

from miners import Miner
from modules import *
from entities import *

class SGMiner(Miner):

    """
        Single mining instance for invoking the sgminer-gm
    """

    def init(self):
        self.miner = 'sgminer'
        self.setupMiner('gpu')
        allowed = UtilExplode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for sgminer miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.amd == 0:
            Logger.printLog('No AMD card found, SGMiner only supports amd card', 'error')
            self.stop()
            self.shutdown()

        self.option = self.option.replace('{sgminer_algo}', self.algo)

        self.setupEnvironment()


    def parse(self, text):

        ## Shorten the text ##
        try:
            regex = r"\[\d+:\d+:\d+\] "
            m = re.search(regex, text)
        except:
            pass

        output = m.group(0)
        text = text.replace(output, '')
        tmp = UtilStripAnsi(text)

        if 'avg' in tmp:
            try:
                regex = r"A:\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('A:', '')
            except:
                pass

            try:
                regex = r"\(avg\):\d+.\d+(M|K)h\/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('(avg):', '')

            except:
                pass

        if ' Diff ' in tmp:
            try:
                regex = r"Diff \d+.\d+/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('Diff ', '')
            except:
                pass

        return text
