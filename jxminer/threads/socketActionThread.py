import io, select, time, json, psutil, re

from entities.job import *
from thread import Thread
from modules.transfer import *
from modules.utility import getHighestTemps, getAverageTemps, calculateStep, printLog, getLogBuffers

class socketActionThread(Thread):

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
        self.active = True
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

        elif action in ('server:status'):
            try:
                self.transfer.send('active')
            except:
                pass

        elif action in ('server:shutdown', 'server:reboot', 'server:update'):
            self.actionCallback(action)


        elif action in ('monitor:miner:cpu'):
            try:
                miner = self.threads.get('cpu_miner').miner
                if miner:
                    self.readMinerBuffer(miner)
            except:
                miner = False
                self.transfer.send('Failed to retrieve miner')
                self.stop()


        elif 'monitor:miner:gpu' in action:
            try:
                miners = self.threads.get('gpu_miner').miners
                x, m, a, i = action.split(':')
                i = int(i)
                miner = miners[i]
            except:
                miner = False
                self.transfer.send('Failed to retrieve miner')
                self.stop()

            if miner:
                self.readMinerBuffer(miner)

        elif 'monitor:server:snapshot' in action:
            try:
                status = self.generateStatusOutput()
                self.transfer.send(json.dumps(status))
            except:
                pass

        elif 'monitor:server' in action:
            while True and self.active:
                try:
                    status = self.generateStatusOutput()
                    self.transfer.send(json.dumps(status))
                    time.sleep(0.5)

                except:
                    self.stop()
                    break


        elif action in ('close'):
            self.stop()

        self.stop()


    def stop(self):
        if self.active:
            try:
                self.connection.close()
                self.parent.remove(self.name)
                status = 'success'
            except:
                status = 'error'
            finally:
                self.active = False
                printLog("Stopping active thread connection", status)



    def destroy(self):
        if self.active:
            try:
                if self.transfer:
                    try:
                        self.transfer.send('Server closing...')
                        self.transfer.wait()
                    except:
                        pass

                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass

                if self.job:
                    self.job.shutdown_flag.set()

                status = 'success'

            except:
                status = 'error'

            finally:
                self.active = False
                printLog("Destroying active thread", status)


    def generateStatusOutput(self) :
        status = dict()
        try:
            if self.config.data.machine.gpu_miner.enable:
                status['general:active:gpu:coin'] = self.config.data.machine.gpu_miner.coin
                status['general:active:gpu:pool'] = self.config.data.machine.gpu_miner.pool
                if self.config.data.machine.gpu_miner.dual:
                    status['general:active:gpu:second_coin'] = self.config.data.machine.gpu_miner.second_coin
                    status['general:active:gpu:second_pool'] = self.config.data.machine.gpu_miner.second_pool
        except:
            pass

        try:
            if self.config.data.machine.cpu_miner.enable:
                status['general:active:cpu:coin'] = self.config.data.machine.cpu_miner.coin
                status['general:active:cpu:pool'] = self.config.data.machine.cpu_miner.pool
        except:
            pass

        try:
            status['general:boxname'] = self.config.data.machine.settings.box_name
        except:
            pass

        try:
            status['temperature:average'] = getAverageTemps(self.gpu)
            status['temperature:highest'] = getHighestTemps(self.gpu)
        except:
            pass

        try:
            for unit in self.fans:
                status['%s:%s:%s' % ('fan', 'speed', unit.index)] = unit.speed
        except:
            pass

        try:
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
        except:
            pass

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
                    key = re.sub('[^0-9]','', temp.label)
                    status['%s:%s:%s:%s' % ('cpu', 'temp', 'label', key)] = temp.label
                    status['%s:%s:%s:%s' % ('cpu', 'temp', 'current', key)] = temp.current
                    status['%s:%s:%s:%s' % ('cpu', 'temp', 'high', key)] = temp.high
                    status['%s:%s:%s:%s' % ('cpu', 'temp', 'critical', key)] = temp.critical
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

        try:
            status['serverlog'] = "\n".join(getLogBuffers())
        except:
            pass

        return status


    def readMinerBuffer(self, miner):
        lastRead = ''
        results = miner.display('all')
        if results:
            for output in results:
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
