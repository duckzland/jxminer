#!/usr/bin/env python

import os, sys, socket, uuid, getopt, signal, time, fcntl

sys.path.append(os.path.dirname(__file__))

from modules import *
from entities import *
from gpu import *
from threads import *

class Main():

    """
        The main class for managing the miner managers
    """

    def detectGPU(self):
        self.cards = []
        c = self.config.data.config
        try:
            nvmlInit()
            deviceCount = nvmlDeviceGetCount()
            self.config.data.dynamic.server.GPU.nvidia = int(deviceCount)
            self.loadXorg()
            for i in range(deviceCount):
                Logger.printLog('Initialized NVidia GPU %s' % (i), 'success')
                self.cards.append(Nvidia(i))
                self.config.data.dynamic.detected.nvidia[i] = i

        except NVMLError:
            self.config.data.dynamic.server.GPU.nvidia = 0
            Logger.printLog('No NVidia GPU found in the system', 'info')

        try:
            devices = listDevices()
            self.config.data.dynamic.server.GPU.amd = int(len(devices))
            if len(devices) < 1:
                raise

            else:
                for i in devices:
                    index = i.replace('card', '')
                    Logger.printLog('Initialized AMD GPU %s' % (index), 'success')

                    gpu = AMD(index)
                    if c.machine.settings.gpu_strict_power_mode:
                        gpu.strictMode = c.machine.settings.gpu_strict_power_mode

                    self.cards.append(gpu)
                    self.config.data.dynamic.detected.amd[index] = index

        except:
            self.config.data.dynamic.server.GPU.amd = 0
            Logger.printLog('No AMD GPU found in the system', 'info')



    def checkTotalGPU(self):
        c = self.config.data.config
        d = self.config.data.dynamic
        if c.machine.gpu_check_total.enable:
            for gpuType in ['amd', 'nvidia']:

                limit       = c.machine.gpu_check_total[gpuType]
                detected    = d.server.GPU[gpuType]
                totalTest   = int(limit) - int(detected)
                box_name    = c.machine.settings.box_name
                rebootDelay = 60

                if int(limit) > 0:
                    if totalTest == 0:
                        Logger.printLog('%s %s gpu initialized properly' % (str(detected), gpuType), 'success')
                        UtilSendSlack('%s %s gpu initialized properly at %s' % (str(detected), gpuType, box_name))

                    else:
                        Logger.printLog('%s %s gpu failed to initialize' % (str(totalTest), gpuType), 'error')
                        UtilSendSlack('%s %s gpu failed to initialize at %s' % (str(totalTest), gpuType, box_name))

                        if c.machine.gpu_check_total.reboot_when_failed:
                            try:
                                Logger.printLog('Rebooting in %d seconds due to %s %s gpu is not initializing properly' % (rebootDelay, str(totalTest), gpuType), 'error')
                                UtilSendSlack('Rebooting %s in %d seconds due to %s %s gpu is not initializing properly' % (rebootDelay, box_name, str(totalTest), gpuType))

                                time.sleep(rebootDelay)
                                os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')

                            # Allow user to cancel the rebooting process
                            except:
                                Logger.printLog('Rebooting cancelled', 'info')
                                UtilSendSlack('Rebooting %s cancelled' % (box_name))



    def detectFans(self):

        blacklisted = self.config.data.config.sensors.blacklisted
        prefix = '/sys/class/hwmon'

        sysfs = SysFS({
            'type': os.path.join(prefix, '%s', 'name'),
            'alt_type': os.path.join(prefix, '%s', 'device', 'name')
        })

        for sensor in os.listdir(prefix) :
            try:
                type = sysfs.get('type', [sensor])
                extra = ''
            except:
                try:
                    type = sysfs.get('alt_type', [sensor])
                    extra = 'device'
                except:
                    continue

            if re.match(r'^hwmon\d+$', sensor) and type not in blacklisted :
                for device in os.listdir(os.path.join(prefix, sensor, extra)) :
                    if re.match(r'^pwm\d+$', device) :
                        Logger.printLog('Initialized fan %s:%s:%s' % (type, sensor, device), 'success')
                        self.fans.append(Fan(device, {
                            'speed': os.path.join(prefix, sensor, extra, '%s'),
                            'pwm': os.path.join(prefix, sensor, extra, '%s_enable'),
                        }))
                        self.config.data.dynamic.detected.fans[device] = device

        if len(self.fans) == 0:
            Logger.printLog('No casing fan found', 'info')



    def loadXorg(self):

        if 'process' in self.xorg or self.config.data.dynamic.server.GPU.nvidia < 1:
            return

        try:
            subprocess.check_output(['pidof', 'Xorg'])
            Logger.printLog('Xorg instance found', 'info')
        except:
            self.xorg['process'] = subprocess.Popen(['X', ':0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.xorg['process'].wait
            self.xorg['proc'] = psutil.Process(self.xorg['process'].pid)

            p = subprocess.Popen(['xrandr', '--setprovideroutputsource', 'modesetting NVIDIA-0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()

            p = subprocess.Popen(['xrandr', '--auto'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()

            Logger.printLog('Loading and tuning Xorg server', 'success')



    def loadThreads(self):

        c = self.config.data.config

        if self.cards and c.fans and self.fans:
            self.threads.process('casing_fans', casingFans(False, self.fans, self.cards), c.fans.casing.enable)

        if self.cards and c.fans:
            self.threads.process('gpu_fans', gpuFans(False, self.cards), c.fans.gpu.enable)

        if self.cards and c.tuner:
            self.threads.process('gpu_tuner', gpuTuner(False, self.cards), c.tuner.settings.enable)
	
        if self.cards and c.notification:
            self.threads.process('notification', notification(False, self.threads, self.fans, self.cards), c.notification.settings.enable)

        if self.cards and c.machine:
            self.threads.process('gpu_miner', gpuMiner(False), c.machine.gpu_miner.enable)

        if c.machine:
            self.threads.process('cpu_miner', cpuMiner(False), c.machine.cpu_miner.enable)

        if c.machine and self.threads.has('gpu_miner'):
            minerManager = self.threads.get('gpu_miner')
            minerManager.selectMiner()
            for miner in minerManager.miners:
                if miner and miner.hasDevFee():
                    self.threads.add('gpu_miner_devfee_removal_%s' % (miner.miner), feeRemoval(False, miner))
                if miner and c.watchdog.settings.enable:
                    self.threads.add('gpu_miner_watchdog_%s' % (miner.miner), watchdog(False, miner, minerManager))

        if c.machine and self.threads.has('cpu_miner'):
            minerManager = self.threads.get('cpu_miner')
            minerManager.selectMiner()
            if minerManager.miner and minerManager.miner.hasDevFee():
                self.threads.add('cpu_miner_devfee_removal_%s' % (minerManager.miner.miner), feeRemoval(False, minerManager.miner))

            if minerManager.miner and c.watchdog.settings.enable:
                self.threads.add('cpu_miner_watchdog', watchdog(False, minerManager.miner, minerManager))

        if c.machine and not self.threads.has('gpu_miner'):
            self.threads.remove('gpu_miner_devfee_removal_')
            self.threads.remove('gpu_miner_watchdog_')

        if c.machine and not self.threads.has('cpu_miner'):
            self.threads.remove('cpu_miner_devfee_removal_')
            self.threads.remove('cpu_miner_watchdog')

        if c.systemd:
            self.threads.process('systemd', systemdWatchdog(False), c.systemd.settings.enable)

        self.threads.start()



    def doAction(self, action):

        if action == 'server:update':
            self.config.scan()
            self.detectGPU()
            self.detectFans()
            self.threads.remove('gpu_tuner')
            self.threads.remove('gpu_fans')
            self.threads.remove('casing_fans')
            self.loadThreads()
            Logger.printLog("Program updated", 'success')

        elif action == 'server:shutdown':
            self.shutdown()

        elif action == 'server:reboot':
            self.threads.destroy()
            self.config.reset()
            self.detectGPU()
            self.detectFans()
            self.loadXorg()
            self.config.scan()
            self.loadThreads()
            Logger.printLog("Program rebooted", 'success')



    def usage(self):
        print 'jxminer -m|-h|-v|-s|-p|-c'
        print '   -m <mode>'
        print '      daemon         Run the program as daemon, logging will be minimized'
        print '   -h Prints this help message'
        print '   -v Prints the server version'
        print '   -s Specify the host this server should bind to'
        print '   -p Specify the port to bind to'
        print '   -c Path to configuration files directory'



    def version(self):
        print '0.6.6'



    def checkArgs(self):
        try:
            opts, args = getopt.getopt(self.argv,"hi:m:s:p:vi:c",["--mode=", "--host=", "--port="])

        except getopt.GetoptError:
            self.usage()
            sys.exit(2)

        self.action = False
        if opts:
            for opt, arg in opts:
                if opt == '-h':
                    self.usage()
                    sys.exit()

                if opt == '-v':
                    self.version()
                    sys.exit()

                if opt in ['-m', '--mode']:
                    self.action = arg

                if opt in ['-s', '--host']:
                    self.host = arg

                if opt in ['-p', '--port']:
                    self.port = int(arg)

                if opt in ['-c']:
                    self.cPath = arg

            if self.action:
                if self.action not in ('daemon'):
                    self.usage()
                    sys.exit(2)



    def checkRoot(self):
        if os.geteuid() != 0:
            Logger.printLog('JXMiner requires root access to modify GPU and Fans properties', 'info')
            os.execvp("sudo", ["sudo"] + sys.argv)



    def checkInstance(self):
        # Only one instance allowed check using pid file and socket
        self.lockfile = open('/var/run/jxminer.pid', 'w+')
        try:
            fcntl.flock(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
        except:
            Logger.printLog('Another instance is running. exiting', 'error')
            os._exit(0)



    def checkConnection(self):
        connection, address = self.socket.accept()
        if connection and address:
            ip, port = str(address[0]), str(address[1])
            self.threads.add(
                'connection_' + str(uuid.uuid4()),
                socketAction(True, connection, self.doAction, self.threads, self.fans, self.cards)
            )
            Logger.printLog("Connecting with %s:%s" % (ip, port), 'success')



    def shutdown(self):

        try:
            self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()

        except:
            pass

        finally:
            Logger.printLog("Closed open sockets", 'success')

        self.threads.destroy()
        Logger.printLog("Stopped running threads", 'success')

        if 'process' in self.xorg:
            self.xorg['process'].kill()
            if psutil.pid_exists(self.xorg['process'].pid):
                self.xorg['proc'].terminate()
                self.xorg['proc'].wait()

            Logger.printLog("Stopped Xorg server", 'success')



    def main(self):

        # Default variables
        self.argv = sys.argv[1:]
        self.host = '127.0.0.1'
        self.port = 8129
        self.cPath = os.path.join('/home', 'jxminer', '.jxminer')
        self.socket_limit = 5
        self.main_tick = 1

        self.checkArgs()
        self.checkRoot()
        self.checkInstance()

        Process = Shutdown()

        try:
            self.logger = Logger(self.action)
            self.config = Config(self.cPath)
            self.config.data.dynamic.settings.mode = self.action
            self.config.scan()
            c = self.config.data.config

            Logger.printLog('Starting Program', 'info')
            UtilSendSlack('%s started JXMiner' % (c.machine.settings.box_name))

            self.fans = []
            self.cards = []
            self.xorg = dict()

            self.detectGPU()
            self.checkTotalGPU()
            self.detectFans()

            self.loadXorg()

            self.threads = Threads()
            self.loadThreads()

            self.socket.listen(self.socket_limit)
            Logger.printLog("Listening to socket with maximum %s connection" % (self.socket_limit), 'success')

            while True:
                if Process.isShuttingDown:
                    Logger.printLog("Shutdown initializing", 'success')
                    break

                self.loadXorg()
                self.threads.clean()
                self.checkConnection()

                time.sleep(self.main_tick)

        except Exception as e:
            Logger.printLog(str(e), 'error')
            Logger.printLog("Preparing to close program", 'info')

        finally:
            self.shutdown()
            UtilSendSlack('%s stopped JXMiner' % (c.machine.settings.box_name))
            Logger.printLog('Exiting main program', 'success')
            os._exit(1)
            os.kill(os.getpid(), signal.SIGINT)



def start_miner():
    Main().main()



if __name__ == "__main__":
    start_miner()
