import re
from miners import Miner
from modules import *
from entities import *

class TRex(Miner):

    """
        Single mining instance for invoking the trex miner
    """

    def init(self):

        self.miner = 'trex'
        self.setupMiner('gpu')
        allowed = UtilExplode(self.miner_config.settings.algo)
        if self.algo not in allowed:
            Logger.printLog('Invalid coin algo for T-Rex miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            Logger.printLog('No Nvidia card found, T-Rex miner only supports Nvidia card', 'error')
            self.stop()
            self.shutdown()

        self.option = self.option.replace('{trex_algo}',self.algo)
        self.setupEnvironment()



    def parse(self, text):

        ## Shorten the text ##
        try:
            regex = r"\d+ \d+:\d+:\d+\ "
            m = re.search(regex, text)
            output = m.group(0)
            if output:
                text = text.replace(output, '')
        except:
            pass

        tmp = UtilStripAnsi(text)

        if 'OK' in tmp:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"- \d+.\d+ (M|k)H\/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('- ', '')

            except:
                pass

        if ', diff ' in tmp:
            try:
                regex = r", diff \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace(', diff ', '')
            except:
                pass

        return text
