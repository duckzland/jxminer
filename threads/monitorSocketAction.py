import sys, pickle, io, select, time, json, psutil
sys.path.append('../')
from entities.job import *
from thread import Thread
from modules.transfer import *
from modules.utility import getHighestTemps, getAverageTemps, calculateStep, printLog

class MonitorSocketAction(Thread):

    def __init__(self, start, Config, connection, actionCallback, JobThreads, FanUnits, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config
        self.connection = connection
        self.actionCallback = actionCallback
        self.threads = JobThreads
        self.fans = FanUnits
        self.gpu = GPUUnits
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(1, self.update)
        self.transfer = Transfer(self.connection)


    def update(self, runner):
        action = None
        try:
            action = self.transfer.recv()
        except:
            self.stop()

        if not action:
            pass

        elif action in ('refresh', 'gpuInfo', 'fansInfo'):
            msg = pickle.dumps(self.actionCallback(action))
            try:
                self.transfer.send(msg)
            except:
                self.stop()

        elif action in ('shutdown', 'reboot', 'update'):
            self.actionCallback(action)

        elif action in ('monitorCpuMiner'):
            try:
                miner = self.threads.get('cpu_miner').miner
            except:
                miner = False
                self.transfer.send('Failed to retrieve miner')
                self.stop()

            if miner:
                self.readMinerBuffer(miner)


        elif 'monitorGpuMiner' in action:
            try:
                miners = self.threads.get('gpu_miner').miners
                a, i = action.split(':')
                i = int(i)
                miner = miners[i]
            except:
                miner = False
                self.transfer.send('Failed to retrieve miner')
                self.stop()

            if miner:
                self.readMinerBuffer(miner)

        elif 'getStatus' in action:
            while True and self.active:
                try:
                    status = dict()
                    status['general:active:gpu:coin'] = self.config['machine'].get('gpu_miner', 'coin')
                    status['general:active:gpu:pool'] = self.config['machine'].get('gpu_miner', 'pool')
                    if self.config['machine'].getboolean('gpu_miner', 'dual'):
                        status['general:active:gpu:second_coin'] = self.config['machine'].get('gpu_miner', 'second_coin')
                        status['general:active:gpu:second_pool'] = self.config['machine'].get('gpu_miner', 'second_pool')

                    status['general:active:cpu:coin'] = self.config['machine'].get('cpu_miner', 'coin')
                    status['general:active:cpu:pool'] = self.config['machine'].get('cpu_miner', 'pool')

                    status['general:boxname'] = self.config['machine'].get('settings', 'box_name')

                    status['temperature:average'] = getAverageTemps(self.gpu)
                    status['temperature:highest'] = getHighestTemps(self.gpu)

                    for unit in self.fans:
                        status['%s:%s:%s' % ('fan', 'speed', unit.index)] = unit.speed

                    totalGPUWatt = float(0.00)
                    for unit in self.gpu:
                        status['%s:%s:%s:%s' % ('gpu', 'fan', unit.type, unit.index)] = unit.fanSpeed
                        status['%s:%s:%s:%s' % ('gpu', 'core', unit.type, unit.index)] = unit.coreLevel
                        status['%s:%s:%s:%s' % ('gpu', 'memory', unit.type, unit.index)] = unit.memoryLevel
                        status['%s:%s:%s:%s' % ('gpu', 'power', unit.type, unit.index)] = unit.powerLevel
                        status['%s:%s:%s:%s' % ('gpu', 'temperature', unit.type, unit.index)] = unit.temperature
                        status['%s:%s:%s:%s' % ('gpu', 'watt', unit.type, unit.index)] = unit.wattUsage
                        totalGPUWatt += float(unit.wattUsage)

                    status['%s:%s' % ('gpu', 'total_watt')] = totalGPUWatt

                    try:
                        miners = self.threads.get('gpu_miner').miners
                        for index, miner in enumerate(miners):
                            status['%s:%s:%s:%s' % ('miner', 'logs', 'gpu', index)] = miner.display('all')
                            minerStats = miner.getStatus()

                            if 'hashrate' in minerStats:
                                status['%s:%s:%s:%s' % ('miner', 'hashrate', 'gpu', index)] = minerStats['hashrate']

                            if 'diff' in minerStats:
                                status['%s:%s:%s:%s' % ('miner', 'diff', 'gpu', index)] = minerStats['diff']

                            if 'shares' in minerStats:
                                status['%s:%s:%s:%s' % ('miner', 'shares', 'gpu', index)] = minerStats['shares']

                    except:
                        pass

                    try:
                        miner = self.threads.get('cpu_miner').miner
                        status['%s:%s:%s' % ('miner', 'logs', 'cpu')] = miner.display('all')
                        minerStats = miner.getStatus()

                        if 'hashrate' in minerStats:
                            status['%s:%s:%s' % ('miner', 'hashrate', 'cpu')] = minerStats['hashrate']

                        if 'diff' in minerStats:
                            status['%s:%s:%s' % ('miner', 'diff', 'cpu')] = minerStats['diff']

                        if 'shares' in minerStats:
                            status['%s:%s:%s' % ('miner', 'shares', 'cpu')] = minerStats['shares']
                    except:
                        pass

                    try:
                        temperatures = psutil.sensors_temperatures()
                        if 'coretemp' in temperatures:
                            temps = temperatures['coretemp']
                            for temp in temps:
                                status['%s:%s:%s:%s' % ('cpu', 'temp', 'current', temp.label)] = temp.current
                                status['%s:%s:%s:%s' % ('cpu', 'temp', 'high', temp.label)] = temp.high
                                status['%s:%s:%s:%s' % ('cpu', 'temp', 'critical', temp.label)] = temp.critical
                    except:
                        pass

                    try:
                        fans = psutil.sensors_fans()
                        if fans:
                            for name, entries in fans.items():
                                for entry in entries:
                                    status['%s:%s:%s' % ('cpu', 'fans', entry.label)] = entry.current
                    except:
                        pass

                    try:
                        frequencies = psutil.cpu_freq(True)
                        if frequencies:
                            for index, frequency in enumerate(frequencies):
                                status['%s:%s:%s:%s' % ('cpu', 'freq', 'current', index)] = frequency.current
                                status['%s:%s:%s:%s' % ('cpu', 'freq', 'min', index)] = frequency.min
                                status['%s:%s:%s:%s' % ('cpu', 'freq', 'max', index)] = frequency.max
                    except:
                        pass

                    try:
                        percentages = psutil.cpu_percent(1, True)
                        if percentages:
                            for index, percentage in enumerate(percentages):
                                status['%s:%s:%s' % ('cpu', 'usage', index)] = percentage
                    except:
                        pass

                    try:
                        virtualMemory = psutil.virtual_memory()
                        if virtualMemory:
                            for type, value in virtualMemory.__dict__.iteritems():
                                status['%s:%s:%s' % ('memory', 'virtual', type)] = value
                    except:
                        pass

                    try:
                        swapMemory = psutil.swap_memory()
                        if swapMemory:
                            for type, value in swapMemory.__dict__.iteritems():
                                status['%s:%s:%s' % ('memory', 'swap', type)] = value
                    except:
                        pass

                    try:
                        diskUsage = psutil.disk_usage('/')
                        if diskUsage:
                            for type, value in diskUsage.__dict__.iteritems():
                                status['%s:%s:%s' % ('disk', 'usage', type)] = value
                    except:
                        pass

                    try:
                        networkStatus = psutil.net_io_counters()
                        if networkStatus:
                            for type, value in networkStatus.__dict__.iteritems():
                                status['%s:%s:%s' % ('network', 'status', type)] = value
                    except:
                        pass

                    self.transfer.send(json.dumps(status))
                    time.sleep(0.5)

                except:
                    self.stop()
                    break


        elif action in ('close'):
            self.stop()

        self.stop()


    def stop(self):
        try:
            self.connection.close()
            self.parent.remove(self.name)

        except:
            pass



    def destroy(self):
        try:
            self.transfer.send('Server closing...')
            self.connection.close()
            if self.job:
                self.job.shutdown_flag.set()
            status = 'success'
        except:
            status = 'error'
        finally:
            self.active = False
            printLog("Stopping active thread", status)



    def readMinerBuffer(self, miner):
        lastRead = ''
        for output in miner.display('all'):
            if output:
                if lastRead != output:
                    self.transfer.send(output)
                    lastRead = output

        while True:
            try:
                output = miner.display('last')
                if output:
                    if lastRead != output:
                        self.transfer.send(output)
                        lastRead = output

                time.sleep(0.5)

            except:
                self.stop()
                break