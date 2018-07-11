import os, subprocess, psutil, time, re, pexpect, signal

from entities.pool import Pool
from modules.transfer import *
from modules.utility import which, getOption, printLog, findFile, explode, stripAnsi

class Miner:

    """
        This is the base class for invoking miner instance
    """

    def __init__(self, Config):
        self.config = Config
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
        name = type + '_miner'
        self.type = type
        self.max_retries = 3
        self.machine = self.config['machine']
        self.coins = self.config['coins']
        self.coin = self.machine.get(name, 'coin')
        self.algo = self.coins.get(self.coin, 'algo')
        self.pool = Pool(self.machine.get(name, 'pool'), self.config)
        self.url = self.pool.getAddress(self.coin)
        self.raw_url = self.pool.getRawAddress(self.coin)
        self.raw_protocol = self.pool.getRawProtocol(self.coin)
        self.port = self.pool.getPort(self.coin)
        self.wallet = self.pool.getWallet(self.coin)
        self.password = self.pool.getPassword(self.coin)
        self.worker = self.machine.get('settings', 'box_name')
        self.email = self.machine.get('settings', 'email')
        self.environment = os.environ.copy()

        if 'gpu' in type and self.machine.getboolean(name, 'dual'):
            self.second_coin = self.machine.get(name, 'second_coin')
            self.second_algo = self.coins.get(self.second_coin, 'algo')
            self.second_pool = Pool(self.machine.get(name, 'second_pool'), self.config)
            self.second_url = self.second_pool.getAddress(self.second_coin)
            self.second_wallet = self.second_pool.getWallet(self.second_coin)

        if hasattr(self, 'miner'):
            self.miner_config = self.config[self.miner]
            self.miner_mode = self.algo

            if hasattr(self, 'second_algo') and self.machine.getboolean(name, 'dual'):
                self.miner_mode = self.miner_mode + '|' + self.second_algo

            default = dict(self.miner_config.items('default'))
            try:
                extra = dict(self.miner_config.items(self.miner_mode))
            # Put exception notice here later
            except:
                extra = False

            self.executable = getOption('executable', default, extra)
            self.option = (
                str(getOption('options', default, extra))
                    .replace('\n', ' #-# ')
                    .replace('{raw_url}', self.raw_url)
                    .replace('{raw_protocol}', self.raw_protocol)
                    .replace('{port}', self.port)
                    .replace('{url}', self.url)
                    .replace('{wallet}', self.wallet)
                    .replace('{password}', self.password)
                    .replace('{worker}', self.worker)
            )

            if 'cpu' in type:
                self.option = (
                    self.option
                        .replace('{thread}', self.machine.get(name, 'thread'))
                        .replace('{priority}', self.machine.get(name, 'priority'))
                )

            if hasattr(self, 'second_coin'):
                self.option = (
                    self.option
                        .replace('{second_url}', self.second_url)
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
        self.status = 'stop'
        path = os.path.join('/usr', 'local')
        if ('machine' in self.config
            and self.config['machine'].has_section('settings')
            and self.config['machine'].has_option('settings', 'executable_location')):
                path = self.config['machine'].get('settings', 'executable_location')

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
            self.monitor()
            self.status = 'ready'
            status = 'success'

        except:
            status = 'error'

        finally:
            printLog('Initializing %s miner instance' % (self.miner), status)



    def stop(self):
        self.status = 'stop'
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

            status = 'success'

        except:
            status = 'error'

        finally:
            printLog('Stopping %s miner instance' % (self.miner), status)



    def check(self):
        if 'ready' in self.status:
            if hasattr(self, 'proc'):
                try:
                    psutil.pid_exists(self.process.pid)
                    self.proc.status() != psutil.STATUS_ZOMBIE
                    alive = True
                except:
                    alive = False
                finally:
                    if not alive:
                        self.stop()
                        time.sleep(5)
                        self.start()
                        self.max_retries = self.max_retries - 1
                        printLog('Restarting crashed %s miner instance' % (self.miner), 'info')
                    else:
                        self.max_retries = 3


            if self.max_retries < 0:
                printLog('Maximum retry of -#%s#- reached' % 3, 'info')
                return 'give_up'

            return 'running'


    def shutdown(self):
        self.status = 'stop'
        try:
            self.stop()
            status = 'success'
        except:
            status = 'error'
        finally:
            printLog('Shutting down %s miner' % (self.miner), status)



    def reboot(self):
        self.stop()
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
        errorCounter = 0;
        lastHashRate = False;
        self.bufferStatus['shares'] = 0

        while True:

            # Too many error, probably the miner hang?
            # or its hashing without shares found
            if errorCounter > 200:
                self.reboot()

            try:
                error = False
                output = p.readline()
                if not output:
                    errorCounter += 1

                else:
                    self.record(output.replace('\r\n', '\n').replace('\r', '\n'))
                    if not self.isHealthy(output):
                        self.reboot()

                    if ('shares' in self.bufferStatus):

                        # Soft checking for miner error
                        # this will just restart the miner
                        if (self.bufferStatus['shares'] == lastHashRate):
                            errorCounter += 1
                            error = True
                        else:
                            lastHashRate = self.bufferStatus['shares']

                    if (error == False):
                        errorCounter = 0

            except:
                errorCounter += 1



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