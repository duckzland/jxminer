import re, os

from miners import Miner
from modules import *
from entities import *

class PhoenixMiner(Miner):

    """
        Single mining instance for invoking the phonix miner
    """

    def init(self):
        self.miner = 'phoenixminer'
        self.setupMiner('gpu')

        if self.algo not in ('ethash'):
            Logger.printLog('Invalid coin algo for phoenix miner', 'error')
            self.stop()
            self.shutdown()

        self.setupEnvironment()


    def parse(self, text):
        self.bufferStatus['diff'] = 'N/A'
        tmp = UtilStripAnsi(text)
        if ' speed: ' in tmp:
            try:
                regex = r"shares: \d+/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('shares: ', '')
            except:
                pass

            try:
                regex = r"speed: \d+.\d*|\d* (?:MH|H)/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('speed: ', '')

            except:
                pass

        return text