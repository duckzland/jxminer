import re

from miners import Miner
from modules import *

class Avermore(Miner):

    """
        Single mining instance for invoking the avermore
    """

    def init(self):
        self.miner = 'avermore'
        self.setupMiner('gpu')
        self.acceptedShares = 0
        self.rejectedShares = 0

        allowed = explode(self.miner_config.settings.algo)

        if self.algo not in allowed:
            raise ValueError('Invalid coin algo for avermore miner')

        if self.config.data.dynamic.server.GPU.amd == 0:
            raise ValueError('No AMD card found, Avermore only supports amd card')

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

        if 'avg' in text:
            try:
                regex = r"\(avg\):\d+.\d+(M|K)h\/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('(avg):', '')

            except:
                pass

        if ' Diff ' in text:
            try:
                regex = r"Diff \d+.\d+/\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('Diff ', '')
            except:
                pass

        # Avermore shares count screwed up use simple counting instead
        if 'Accepted' in text:
            self.acceptedShares += 1

        if 'Rejected' in text:
            self.rejectedShares += 1

        self.bufferStatus['shares'] = '%s/%s' % (self.acceptedShares, self.rejectedShares)

        return text