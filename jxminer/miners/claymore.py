import re, os
from miners import Miner
from modules import *
from entities import *

class Claymore(Miner):

    """
        Single mining instance for invoking the claymore miner and its variation
    """

    def init(self):
        self.miner = 'claymore'
        self.setupMiner('gpu')

        if self.algo not in ('ethash', 'equihash', 'cryptonight7', 'cryptonight'):
            Logger.printLog('Invalid coin algo for claymore miner', 'error')
            self.stop()
            self.shutdown()

        if hasattr(self, 'second_algo') and self.second_algo not in ('blake2s'):
            Logger.printLog('Invalid secondary coin algo for claymore dual miner', 'error')
            self.stop()
            self.shutdown()

        if self.algo in ('equihash', 'cryptonight', 'cryptonight7') and self.config.data.dynamic.server.GPU.amd == 0:
            Logger.printLog('No AMD card found, Claymore miner for % only support AMD card', 'error')
            self.stop()
            self.shutdown()

        if self.coin not in 'eth':
            self.option = (
                self.option
                    .replace('{allcoins}', '1')
                    .replace('{nofee}',    '1')
            )
        else:
            self.option = (
                self.option
                    .replace('{allcoins}', '0')
                    .replace('{nofee}',    '0')
            )

        if self.algo in ('ethash', 'equihash') and self.miner_config.settings.devFeeRemoval:
            self.hasFee          = True
            self.listening_ports = []
            self.dev_pool_ports  = [14444,4444,3333,9999,5000,5005,8008,20535,20536,20537]

        self.setupEnvironment()


    def parse(self, text):
        self.bufferStatus['diff'] = 'N/A'
        tmp = UtilStripAnsi(text)
        if 'Total' in tmp:
            try:
                regex = r"Total Shares: \d+, Rejected: \d+"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['shares'] = output.replace('Total Shares: ', '').replace(', ', '/').replace('Rejected: ', '')
            except:
                pass

            try:
                regex = r"Total Speed: \d+.\d*|\d* (?:Mh|H)/s"
                m = re.search(regex, tmp)
                output = m.group(0)
                if output:
                    self.bufferStatus['hashrate'] = output.replace('Total Speed: ', '')

            except:
                pass

        return text


    def processFeePayload(self, FeeRemoval, arg1, payload, payload_text, pkt):
        if 'submitLogin' in payload_text:
            if FeeRemoval.wallet not in payload_text:
                payload_text = re.sub(r'0x.{40}', FeeRemoval.wallet, payload_text)
                return payload_text

        return False


    def reboot(self):
        # AMD need full server reboot when hang
        if self.config.data.dynamic.server.GPU.amd > 0:
            # If we are here probably server crashed badly, invoke hard reboot
            os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')
        else:
            self.stop()
            self.start()