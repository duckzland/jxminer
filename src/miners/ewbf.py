import sys, os, subprocess, psutil, time, re
sys.path.append('../')
from miners.miner import Miner
from modules.utility import which, getOption, printLog, findFile, explode, stripAnsi

class EWBF(Miner):

    """
        Single mining instance for invoking the ewbf miner
    """

    def init(self):
        self.miner = 'ewbf'
        self.setupMiner('gpu')
        self.checkKeywords = []

        if self.algo not in ('equihash'):
            raise ValueError('Invalid coin algo for ewbf miner')

        if self.config['server'].getint('GPU', 'nvidia') == 0:
            raise ValueError('No Nvidia card,  ewbf miner only support Nvidia card')

        self.setupEnvironment()



    def parse(self, text):
        if 'Accepted share' in text:
            try:
                regex = r"[A:\d+, R:\d+]"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('[A:', '').replace(', ', '/').replace('R:', '').replace(']', '')
            except:
                pass

        if 'Total speed:' in text:
            try:
                regex = r"\d+.\d+ Sol/s"
                m = re.search(regex, text)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output

            except:
                pass

        return text