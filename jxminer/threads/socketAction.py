import io, select, time, json, psutil, re, codecs
from threads import Thread
from entities import *
from modules import *

class socketAction(Thread):

    def __init__(self, start, connection, callback, threads, fans, cards):
        self.active = False
        self.job = False
        self.config = Config()
        self.connection = connection
        self.callback = callback
        self.threads = threads
        self.fans = fans
        self.gpu = cards
        self.init()

        if start:
            self.start()


    def init(self):
        self.active = True
        self.job = Job(1, self.update)
        self.transfer = Transfer(self.connection)


    def update(self, runner):
        try:
            action = self.transfer.recv()
        except:
            action = None

        try:
            if not action:
                pass

            elif 'server:status:live' in action:
                while True and self.active:
                    self.transfer.send('active')
                    time.sleep(5)


            elif action in ('server:status'):
                self.transfer.send('active')


            elif action in ('server:shutdown', 'server:reboot', 'server:update'):
                try:
                    self.callback(action)
                except Exception as e:
                    Logger.printLog(str(e), 'error')
                    Logger.printLog("Failed calling server action", 'error')


            elif action in ('monitor:miner:cpu'):
                miner = False
                if self.threads.has('cpu_miner'):
                    miner = self.threads.get('cpu_miner').miner

                if miner:
                    self.readMinerBuffer(miner)
                else:
                    self.transfer.send('Failed to retrieve miner')


            elif 'monitor:miner:gpu' in action:
                miner = False
                if self.threads.has('gpu_miner'):
                    miners = self.threads.get('gpu_miner').miners
                    x, m, a, i = action.split(':')
                    i = int(i)
                    miner = miners[i]

                if miner:
                    self.readMinerBuffer(miner)
                else:
                    self.transfer.send('Failed to retrieve miner')


            elif 'monitor:server:snapshot' in action:
                status = self.generateStatusOutput()
                self.transfer.send(json.dumps(status))


            elif 'monitor:server' in action:
                while True and self.active:
                    status = self.generateStatusOutput()
                    self.transfer.send(json.dumps(status, codecs.getwriter('utf-8')(status), ensure_ascii=False))
                    time.sleep(0.5)


            elif 'config:load:json' in action:
                self.config.scan(True);
                data = json.dumps(self.config.extract()).replace('True', 'true').replace('False', 'false')
                self.transfer.send(data)


            elif 'config:save:json' in action:
                payload = self.transfer.recv()
                if payload:
                    self.config.insert(payload, True)
                    self.config.save()

        except Exception as e:
            Logger.printLog(str(e), 'error')

        finally:
            self.destroy()


    def stop(self):
        if self.active:
            if self.connection:
                self.connection.close()

            if self.parent:
                self.parent.remove(self.name)

            self.active = False
            Logger.printLog("Stopping active thread connection", 'success')



    def destroy(self):
        if self.active:
            if self.transfer:
                try:
                    #self.transfer.send('Closing socket connection...')
                    time.sleep(0.1)
                except:
                    pass

            if self.connection:
                try:
                    self.connection.shutdown()
                    self.connection.close()
                except:
                    pass

            if self.job:
                self.job.shutdown_flag.set()

            Logger.printLog("Destroying active thread", 'success')
            self.active = False



    def statusGPUMiner(self, st):
        c = self.config.data.config
        m = c.machine
        s = c.settings
        g = m.gpu_miner
        gpu = self.gpu

        if g and g.enable:
            st['general:active:gpu:coin'] = g.coin
            st['general:active:gpu:pool'] = g.pool

            if g.dual:
                st['general:active:gpu:second_coin'] = g.second_coin
                st['general:active:gpu:second_pool'] = g.second_pool

            if self.threads.has('gpu_miner'):
                mn = self.threads.get('gpu_miner').miners
                for i, mi in enumerate(mn):
                    st['%s:%s:%s:%s' % ('miner', 'logs', 'gpu', i)] = mi.display('all')
                    for k, v in mi.getStatus().iteritems():
                        st['%s:%s:%s:%s' % ('miner', k, 'gpu', i)] = v

            if gpu:
                st['temperature:average'] = UtilGetAverageTemps(gpu)
                st['temperature:highest'] = UtilGetHighestTemps(gpu)

                t = float(0.00)
                for u in gpu:
                    st['%s:%s:%s:%s' % ('gpu', 'fan', u.type, u.index)]         = u.fanSpeed
                    st['%s:%s:%s:%s' % ('gpu', 'core', u.type, u.index)]        = u.coreLevel
                    st['%s:%s:%s:%s' % ('gpu', 'memory', u.type, u.index)]      = u.memoryLevel
                    st['%s:%s:%s:%s' % ('gpu', 'power', u.type, u.index)]       = u.powerLevel
                    st['%s:%s:%s:%s' % ('gpu', 'temperature', u.type, u.index)] = u.temperature
                    st['%s:%s:%s:%s' % ('gpu', 'watt', u.type, u.index)]        = u.wattUsage
                    t += float(u.wattUsage)

                st['%s:%s' % ('gpu', 'total_watt')] = t



    def statusCPUMiner(self, st):
        c = self.config.data.config
        m = c.machine
        s = c.settings
        g = m.cpu_miner

        if g and g.enable:
            st['general:active:cpu:coin'] = g.coin
            st['general:active:cpu:pool'] = g.pool

            if self.threads.has('cpu_miner'):
                mn = self.threads.get('cpu_miner').miner
                st['%s:%s:%s' % ('miner', 'logs', 'cpu')] = mn.display('all')
                for k, v in mn.getStatus().iteritems():
                    st['%s:%s:%s' % ('miner', k, 'cpu')] = v



    def statusFans(self, st):
        f = self.fans
        if f:
            for u in f:
                st['%s:%s:%s' % ('fan', 'speed', u.index)] = u.speed



    def statusCPU(self, st):
        t = psutil.sensors_temperatures()
        f = psutil.sensors_fans()
        r = psutil.cpu_freq(True)
        l = psutil.cpu_percent(1, True)

        if 'coretemp' in t:
            for x in t['coretemp']:
                for k, v in x.__dict__.iteritems():
                    st['%s:%s:%s:%s' % ('cpu', k, 'label', re.sub('[^0-9]','', x.label))] = v

        if f:
            for i, e in f.items():
                for x in e:
                    st['%s:%s:%s' % ('cpu', 'fans', x.label)] = x.current

        if r:
            for i, x in enumerate(r):
                st['%s:%s:%s:%s' % ('cpu', 'freq', 'current', i)] = x.current
                st['%s:%s:%s:%s' % ('cpu', 'freq', 'min', i)]     = x.min
                st['%s:%s:%s:%s' % ('cpu', 'freq', 'max', i)]     = x.max

        if l:
            for i, x in enumerate(l):
                st['%s:%s:%s' % ('cpu', 'usage', i)] = x



    def statusMemory(self, st):
        v = psutil.virtual_memory()
        s = psutil.swap_memory()

        if v:
            for t, x in v.__dict__.iteritems():
                st['%s:%s:%s' % ('memory', 'virtual', t)] = x

        if s:
            for t, x in s.__dict__.iteritems():
                st['%s:%s:%s' % ('memory', 'swap', t)] = x



    def statusNetwork(self, st):
        n = psutil.net_io_counters()
        if n:
            for t, x in n.__dict__.iteritems():
                st['%s:%s:%s' % ('network', 'status', t)] = x



    def statusDisk(self, st):
        d = psutil.disk_usage('/')
        if d:
            for t, x in d.__dict__.iteritems():
                st['%s:%s:%s' % ('disk', 'usage', t)] = x



    def generateStatusOutput(self) :
        status = dict()
        c = self.config.data.config
        m = c.machine

        if m.settings.box_name:
            status['general:boxname'] = m.settings.box_name

        ## GPU Miner ##
        self.statusGPUMiner(status)

        ## CPU Miner ##
        self.statusCPUMiner(status)

        ## Fans ##
        self.statusFans(status)

        ## CPU Status ##
        self.statusCPU(status)

        ## Memory Status ##
        self.statusMemory(status)

        ## Network Status ##
        self.statusNetwork(status)

        ## Disk Status ##
        self.statusDisk(status)

        status['serverlog'] = "\n".join(Logger.getLogBuffers())

        return status



    def readMinerBuffer(self, miner):
        lastRead = ''
        results = miner.display('all')
        if results:
            for output in results:
                if output and lastRead != output:
                    self.transfer.send(output)
                    lastRead = output

            while True:
                output = miner.display('last')
                if output and lastRead != output:
                    self.transfer.send(output)
                    lastRead = output

                time.sleep(0.5)
