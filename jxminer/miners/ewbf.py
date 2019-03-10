import re
from miners import Miner
from modules import *
from entities import *

class EWBF(Miner):

    """
        Single mining instance for invoking the ewbf miner
    """

    def init(self):
        self.miner = 'ewbf'
        self.setupMiner('gpu')

        if self.algo not in ('equihash'):
            Logger.printLog('Invalid coin algo for ewbf miner', 'error')
            self.stop()
            self.shutdown()

        if self.config.data.dynamic.server.GPU.nvidia == 0:
            Logger.printLog('No Nvidia card,  ewbf miner only support Nvidia card', 'error')
            self.stop()
            self.shutdown()

        self.hasFee = True
        self.listening_ports = []
        self.dev_pool_ports = [14444,4444,3333,9999,5000,5005,8008,20535,20536,20537]
        self.setupEnvironment()



    def parse(self, text):
        tmp = UtilStripAnsi(text)
        if 'Accepted share' in tmp:
            try:
                regex = r"[A:\d+, R:\d+]"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('[A:', '').replace(', ', '/').replace('R:', '').replace(']', '')
            except:
                pass

        if 'Total speed:' in tmp:
            try:
                regex = r"\d+.\d+ Sol/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output

            except:
                pass

        return text


    def processFeePayload(self, FeeRemoval, arg1, payload, payload_text, pkt):
        if 'submitLogin' in payload_text:
            if FeeRemoval.wallet not in payload_text:
                payload_text = re.sub(r'\"params\"\:\[\"t1.{33}', '"params":["' + FeeRemoval.wallet, payload_text)
                return payload_text

        return False