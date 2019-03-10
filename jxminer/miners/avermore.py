import re

from miners import Miner
from modules import *
from entities import *

class Avermore(Miner):

    """
        Single mining instance for invoking the avermore
    """

    def init(self):
        self.miner = 'avermore'
        self.setupMiner('gpu')
        self.acceptedShares = 0
        self.rejectedShares = 0

        allowed = UtilExplode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for avermore', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.amd == 0:
            Logger.printLog('No AMD card found, Avermore only supports amd card', 'error')
            self.stop()
            self.shutdown()

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

        # Avermore shares count screwed up use simple counting instead
        if 'Accepted' in tmp:
            self.acceptedShares += 1

        if 'Rejected' in tmp:
            self.rejectedShares += 1

        self.bufferStatus['shares'] = '%s/%s' % (self.acceptedShares, self.rejectedShares)

        return text