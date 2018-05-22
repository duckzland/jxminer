import re
from miners.miner import Miner

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

        self.hasFee = True
        self.listening_ports = []
        self.dev_pool_ports = [14444,4444,3333,9999,5000,5005,8008,20535,20536,20537]
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


    def processFeePayload(self, FeeRemoval, arg1, payload, payload_text, pkt):
        if 'submitLogin' in payload_text:
            if FeeRemoval.wallet not in payload_text:
                payload_text = re.sub(r'\"params\"\:\[\"t1.{33}', '"params":["' + FeeRemoval.wallet, payload_text)
                return payload_text

        return False