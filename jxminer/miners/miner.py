import os, subprocess, psutil, time, re, pexpect, signal

from entities.pool import Pool
from entities.config import Config
from modules.transfer import *
from modules.utility import which, getOption, printLog, findFile, explode, stripAnsi

class Miner:

    """
        This is the base class for invoking miner instance
    """

    def __init__(self):
        self.config = Config()
        self.status = 'stop'
        self.checkKeywords = []
        self.buffers = []
        self.bufferStatus = dict()
        self.bufferStatus['diff'] = 0
        self.bufferStatus['hashrate'] = 0
        self.bufferStatus['shares'] = 0
        self.hasFee = False
        self.init()


    def init(self):
        pass


    def processFeePayload(self, FeeRemoval, arg1, payload):
        pass


    def setupMiner(self, type):
        c                   = self.config.data.config
        name                = type + '_miner'
        self.type           = type
        self.max_retries    = 3
        self.machine        = c.machine
        self.coins          = c.coins
        self.coin           = c.machine[name].coin
        self.algo           = c.coins[self.coin].algo
        self.worker         = c.machine.settings.worker
        self.email          = c.machine.settings.email
        self.wd_hashrate    = c.machine[name].minimum_hashrate
        self.environment    = os.environ.copy()

        self.pool           = Pool(c.machine[name].pool)
        self.url            = self.pool.getAddress(self.coin)
        self.raw_url        = self.pool.getRawAddress(self.coin)
        self.raw_protocol   = self.pool.getRawProtocol(self.coin)
        self.port           = self.pool.getPort(self.coin)
        self.wallet         = self.pool.getWallet(self.coin)
        self.password       = self.pool.getPassword(self.coin)

        if 'gpu' in type and c.machine[name].dual:
            self.second_coin    = c.machine[name].second_coin
            self.second_algo    = self.coins[self.second_coin].algo
            self.second_pool    = Pool(self.machine[name].second_pool)
            self.second_url     = self.second_pool.getAddress(self.second_coin)
            self.second_wallet  = self.second_pool.getWallet(self.second_coin)

        if hasattr(self, 'miner'):
            self.miner_config   = self.config.data.miners[self.miner]
            self.miner_mode     = self.algo

            if hasattr(self, 'second_algo') and self.machine[name].dual:
                self.miner_mode = self.miner_mode + '|' + self.second_algo

            default = self.miner_config.settings
            try:
                extra = self.miner_config[self.miner_mode]
            # Put exception notice here later
            except:
                extra = False

            self.executable = getOption('executable', default, extra)
            self.option = (
                str(getOption('options', default, extra))
                    .replace('\n',              ' #-# ')
                    .replace('{raw_url}',       self.raw_url)
                    .replace('{raw_protocol}',  self.raw_protocol)
                    .replace('{port}',          self.port)
                    .replace('{url}',           self.url)
                    .replace('{wallet}',        self.wallet)
                    .replace('{password}',      self.password)
                    .replace('{worker}',        self.worker)
            )

            if 'cpu' in type:
                self.option = (
                    self.option
                        .replace('{thread}',    self.machine[name].thread)
                        .replace('{priority}',  self.machine[name].priority)
                )

            if hasattr(self, 'second_coin'):
                self.option = (
                    self.option
                        .replace('{second_url}',    self.second_url)
                        .replace('{second_wallet}', self.second_wallet)
                )



    def setupEnvironment(self):
        env = os.environ.copy()
        #python env wants string instead of int!
        env['GPU_FORCE_64BIT_PTR'] = '1'
        env['GPU_MAX_HEAP_SIZE'] = '100'
        env['GPU_USE_SYNC_OBJECTS'] = '1'
        env['GPU_MAX_ALLOC_PERCENT'] = '100'
        env['GPU_SINGLE_ALLOC_PERCENT'] = '100'
        self.environment = env



    def start(self):
        if self.status == 'stop':
            c    = self.config.data.config
            path = os.path.join('/usr', 'local')

            if c.machine.settings.executable_location:
                path = c.machine.settings.executable_location

            command = findFile(path, self.executable)

            args = []
            for arg in explode(self.option, ' #-# '):
                for single in explode(arg, ' '):
                    args.append(single)

            try:
                self.process = pexpect.spawn(
                    command,
                    self.setupArgs(args),
                    env=self.environment,
                    timeout=None,
                    cwd=os.path.dirname(command)
                )
                self.proc = psutil.Process(self.process.pid)
                self.status = 'ready'
                status = 'success'

            except:
                status = 'error'

            finally:
                printLog('Initializing %s miner instance' % (self.miner), status)

        if self.status == 'ready':
            self.monitor()



    def stop(self):
        if self.status == 'ready':
            try:
                self.process.terminate(True)
                self.process.wait()

                # Maybe redundant
                if psutil.pid_exists(self.process.pid):
                    self.proc.terminate()
                    self.proc.wait()

                # This is most probably redundant
                if psutil.pid_exists(self.process.pid):
                    os.kill(self.process.pid, signal.SIGINT)

                self.status = 'stop'
                status = 'success'

            except:
                status = 'error'

            finally:
                printLog('Stopping %s miner instance' % (self.miner), status)



    def check(self):
        if self.status == 'ready':
            if hasattr(self, 'proc'):
                try:
                    if psutil.pid_exists(self.process.pid) and self.proc.status() != psutil.STATUS_ZOMBIE:
                        alive = True

                except:
                    alive = False

                finally:
                    if not alive:
                        self.reboot()
                        self.max_retries = self.max_retries - 1
                        printLog('Restarting crashed %s miner instance' % (self.miner), 'info')
                    else:
                        self.max_retries = 3


            if self.max_retries < 0:
                printLog('Maximum retry of -#%s#- reached' % 3, 'info')
                return 'give_up'

            return 'running'



    def shutdown(self):
        try:
            self.stop()
            status = 'success'
        except:
            status = 'error'
        finally:
            printLog('Shutting down %s miner' % (self.miner), status)



    def reboot(self):
        self.stop()
        time.sleep(5)
        self.start()



    def record(self, text):
        if len(self.buffers) > 10:
            self.buffers.pop(0)

        self.buffers.append(self.parse(text))



    def isHealthy(self, text):
        healthy = True
        for key in self.checkKeywords:
            healthy = key not in text
            if not healthy:
                break
        return healthy



    def monitor(self):
        p = self.process
        while True:
            try:
                error = False
                output = p.readline()
                if output:
                    self.record(output.replace('\r\n', '\n').replace('\r', '\n'))

                    if not self.isHealthy(output):
                        self.minerSickAction()
                        break

            except:
                pass

            time.sleep(1)



    def minerSickAction(self):
        self.reboot()



    def parse(self, text):
        return text



    def display(self, lines = 'all'):
        result = None
        if self.buffers:
            if lines == 'all':
                result = self.buffers

            elif lines == 'last':
                result = self.buffers[-1]

            elif lines == 'first':
                result = self.buffers[0]

        return result



    def getStatus(self):
        return self.bufferStatus



    def hasDevFee(self):
        return self.hasFee


    def setupArgs(self, args):
        return args