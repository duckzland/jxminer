import re
from miners import Miner
from modules import *
from entities import *

class CastXmr(Miner):

    """
        Single mining instance for invoking the castxmr
    """

    def init(self):

        self.miner = 'castxmr'
        self.setupMiner('gpu')

        allowed = UtilExplode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for CastXMR miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.amd == 0:
            Logger.printLog('No AMD card found, CastXMR only supports AMD card', 'error')
            self.stop()
            self.shutdown()

        gpuNumber = ','.join(map(str, range(0, self.config.data.dynamic.server.GPU.amd)))

        self.option = self.option.replace('{castxmr_gpu}', gpuNumber)
        self.setupEnvironment()




    def parse(self, text):
        tmp = UtilStripAnsi(text)
        if 'Shares:' in tmp:
            try:
                regex = r"Shares: \d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('Shares: ', '')
            except:
                pass

            try:
                regex = r"Hash Rate Avg: \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff ', '')
            except:
                pass

            try:
                regex = r", \d+.\d+( M| k| )H"
                regex = r"Hash Rate Avg: \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('Hash Rate Avg: ', '')

            except:
                pass


        if 'Difficulty changed. Now: ' in tmp:
            self.bufferStatus['diff'] = tmp.replace('Difficulty changed. Now: ', '')

        return text