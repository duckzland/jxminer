import time, json, psutil
from threads import Thread
from entities import *
from modules import *

from addict import Dict
from websocket import create_connection

class notification(Thread):

    def __init__(self, **kwargs):
        super(notification, self).__init__()
        self.configure(**kwargs)


    def init(self):
        self.settings = self.config.data.config.notification.settings
        self.threads = self.args.get('threads', False)
        self.fans = self.args.get('fans', False)
        self.gpu = self.args.get('cards', False)
        self.url = self.settings.server.url
        self.port = self.settings.server.port

        self.setPauseTime(self.settings.tick)

        if self.args.get('start', False):
            self.start()


    def update(self, runner):

        status = Dict()

        ## General Machine information ##
        try:
            machine = self.config.data.config.machine
            status.general.boxname = machine.settings.box_name
        except:
            pass

        try:
            if machine.gpu_miner.enable:
                status.general.active.gpu.coin = machine.gpu_miner.coin
                status.general.active.gpu.pool = machine.gpu_miner.pool
                if machine.gpu_miner.dual:
                    status.general.active.gpu.second_coin = machine.gpu_miner.second_coin
                    status.general.active.gpu.second_pool = machine.gpu_miner.second_pool
        except:
            pass

        try:
            if machine.cpu_miner.enable:
                status.general.active.cpu.coin = machine.cpu_miner.coin
                status.general.active.cpu.pool = machine.cpu_miner.pool
        except:
            pass


        ## GPU Information ##
        try:
            totalGPUWatt = float(0.00)
            for unit in self.gpu:
                status.gpu.units[unit.type][unit.index].fan = unit.fanSpeed
                status.gpu.units[unit.type][unit.index].core = unit.coreLevel
                status.gpu.units[unit.type][unit.index].memory = unit.memoryLevel
                status.gpu.units[unit.type][unit.index].power = unit.powerLevel
                status.gpu.units[unit.type][unit.index].temperature = unit.temperature
                status.gpu.units[unit.type][unit.index].watt = unit.wattUsage
                totalGPUWatt += float(unit.wattUsage)

            status.gpu.total_unit = len(self.gpu)
            status.gpu.total_watt = totalGPUWatt
            status.gpu.temperature.average = UtilGetAverageTemps(self.gpu)
            status.gpu.temperature.highest = UtilGetHighestTemps(self.gpu)

        except:
            pass

        ## Casing Fans ##
        try:
            for unit in self.fans:
                status.fans.speed[unit.index] = unit.speed
        except:
            pass


        ## GPU miners stats ##
        try:
            miners = self.threads.get('gpu_miner').miners
            for index, miner in enumerate(miners):
                status.miner.logs.gpu[index] = miner.display('all')
                minerStats = miner.getStatus()

                if 'hashrate' in minerStats:
                    status.miner.hashrate.gpu[index] = minerStats['hashrate']

                if 'diff' in minerStats:
                    status.miner.diff.gpu[index] = minerStats['diff']

                if 'shares' in minerStats:
                    status.miner.shares.gpu[index] = minerStats['shares']
        except:
            pass

        ## CPU miner stats ##
        try:
            miner = self.threads.get('cpu_miner').miner
            status.miner.logs.cpu[index] = miner.display('all')
            minerStats = miner.getStatus()

            if 'hashrate' in minerStats:
                status.miner.hashrate.cpu[index] = minerStats['hashrate']

            if 'diff' in minerStats:
                status.miner.diff.cpu[index] = minerStats['diff']

            if 'shares' in minerStats:
                status.miner.shares.cpu[index] = minerStats['shares']
        except:
            pass

        ## Computer Statuses ##
        try:
            temperatures = psutil.sensors_temperatures()
            if 'coretemp' in temperatures:
                temps = temperatures['coretemp']
                for temp in temps:
                    status.cpu.temperature.current[temp.label] = temp.current
                    status.cpu.temperature.high[temp.label] = temp.high
                    status.cpu.temperature.critical[temp.label] = temp.critical
        except:
            pass

        try:
            fans = psutil.sensors_fans()
            if fans:
                for name, entries in fans.items():
                    for entry in entries:
                        status.cpu.fans[entry.label] = entry.current
        except:
            pass

        try:
            frequencies = psutil.cpu_freq(True)
            if frequencies:
                status.cpu.frequencies = frequencies
        except:
            pass

        try:
            percentages = psutil.cpu_percent(1, True)
            if percentages:
                status.cpu.usage = percentages
        except:
            pass

        try:
            virtualMemory = psutil.virtual_memory()
            if virtualMemory:
                for type, value in virtualMemory.__dict__.iteritems():
                    status.memory.virtual[type] = value
        except:
            pass

        try:
            swapMemory = psutil.swap_memory()
            if swapMemory:
                for type, value in swapMemory.__dict__.iteritems():
                    status.memory.swap[type] = value
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
                    status.network.status[type] = value
        except:
            pass

        try:
            status.serverlog = "\n".join(Logger.getLogBuffers())
        except:
            pass

        try:
            ws = create_connection("ws://%s:%s/" % (self.url, self.port))
            ws.send(json.dumps(status))
            ws.close()
        except:
            self.setPauseTime(20)


    def destroy(self):
        self.stop()
        Logger.printLog("Stopping Notification manager", 'success')
