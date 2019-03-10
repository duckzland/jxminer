import re

from miners import Miner
from modules import *
from entities import *

class CpuMiner(Miner):

    """
        Single mining instance for invoking the cpuminer-opt miner and its variation

        Notice
        ======
            cpuminer-opt might not work with old CPU (eg. pentium duo and below), recompilation might be needed
            to support the older generation CPU

        Configuration
        =============
            Configuration file for the miner options and supported algorithm is located at data/miners/cpuminer.ini
    """

    def init(self):
        self.miner = 'cpuminer'
        self.setupMiner('cpu')
        allowed = UtilExplode(self.miner_config.settings.algo)
        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for cpuminer miner', 'error')
            self.stop()
            self.shutdown()

        self.option = self.option.replace('{cpuminer_algo}', self.algo)


    def parse(self, text):
        tmp = UtilStripAnsi(text)
        self.bufferStatus['diff'] = ''
        if 'Accepted' in tmp:
            try:
                regex = r"Accepted \d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

        if 'speed' in tmp:
            try:
                regex = r"H, \d+.\d+ (?:MH|H)/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('H, ', '')

            except:
                pass

        return text