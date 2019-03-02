import re

from miners import Miner
from modules import *

class AmdXMRig(Miner):

    """
        Single mining instance for invoking the xmrig amd miner
    """

    def init(self):
        self.miner = 'amdxmrig'
        self.setupMiner('gpu')
        self.checkKeywords = []

        allowed = [
            'cryptonight',
            'cryptonight7',
            'cryptonight7-v3',
            'cryptonight7-v4',
            'cryptonight7-v8',
            'cryptonight-ipbc',
            'cryptonight-lite',
            'cryptonight-heavy',
            'cryptonight-v1',
            'cryptonight-lite-v1',
            'cryptonight-heavy-v1'
        ]

        if self.algo not in allowed:
            raise ValueError('Invalid coin algo for xmrig amd miner')

        if self.config.data.dynamic.server.GPU.amd == 0:
            raise ValueError('No AMD card found, AMD XMRig miner only support AMD card')

        devices = []
        for i in range(0, int(self.config.data.dynamic.server.GPU.amd)):
            for x in range(0, int(self.miner_config.settings.threads)):
                devices.append(str(i))

        self.option = self.option.replace('{xmrig_devices}', ','.join(devices))

        if 'intensity' in self.miner_config.settings:
            self.option = self.option.replace('{xmrig_intensity}', self.miner_config.settings.intensity)

        self.setupEnvironment()



    def parse(self, text):
        tmp = stripAnsi(text)
        if 'accepted' in tmp:
            try:
                regex = r"\d+\/\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output
            except:
                pass

            try:
                regex = r"diff \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['diff'] = output.replace('diff ', '')
            except:
                pass

        if 'speed' in tmp:
            try:
                regex = r"15m \d+.\d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('15m ', '')

            except:
                pass

        return text
