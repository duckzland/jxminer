import re
from miners.miner import Miner
from modules.utility import explode

class TRex(Miner):

    """
        Single mining instance for invoking the trex miner
    """

    def init(self):

        self.miner = 'trex'
        self.setupMiner('gpu')
        self.checkKeywords = [
            'the launch timed out and was terminated'
        ]

        allowed = explode(self.miner_config.settings.algo)

        miner_algo = self.algo

        if miner_algo not in allowed:
            raise ValueError('Invalid coin algo for T-Rex miner')

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            raise ValueError('No Nvidia card found, T-Rex miner only supports Nvidia card')

        self.option = self.option.replace('{trex_algo}', miner_algo)
        self.setupEnvironment()



    def parse(self, text):

        ## Shorten the text ##
        regex = r"\d+ \d+:\d+:\d+\ "
        m = re.search(regex, text)
        output = m.group(0)
        text = text.replace(output, '')

        if 'OK' in text:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"- \d+.\d+ (M|k)H\/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('- ', '')

            except:
                pass

        if ', diff ' in text:
            try:
                regex = r", diff \d+.\d+"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace(', diff ', '')
            except:
                pass

        return text