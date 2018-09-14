#!/usr/bin/env python

import os, sys, traceback, ConfigParser, socket, uuid, getopt, signal, time, fcntl

# Registering main root path for sane building!
sys.path.append(os.path.dirname(__file__))

from modules.pynvml import *
from modules.rocmsmi import *
from modules.sysfs import *
from modules.utility import sendSlack, insertConfig

from entities.nvidia import *
from entities.amd import *
from entities.fan import *
from entities.threads import *
from entities.shutdown import *
from entities.config import *
from entities.logger import *

from threads.casingFansThread import *
from threads.gpuFansThread import *
from threads.gpuTunerThread import *
from threads.socketActionThread import *
from threads.gpuMinerThread import *
from threads.cpuMinerThread import *
from threads.systemdThread import *
from threads.feeRemovalThread import *
from threads.notificationThread import *
from threads.watchdogThread import *

class Main():

    "This is the base class for GPU instance"

    def detectGPU(self):
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
                    self.cards.append(AMD(index))
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
                        sendSlack('%s %s gpu initialized properly at %s' % (str(detected), gpuType, box_name))

                    else:
                        Logger.printLog('%s %s gpu failed to initialize' % (str(totalTest), gpuType), 'error')
                        sendSlack('%s %s gpu failed to initialize at %s' % (str(totalTest), gpuType, box_name))

                        if c.machine.gpu_check_total.reboot_when_failed:
                            try:
                                Logger.printLog('Rebooting in %d seconds due to %s %s gpu is not initializing properly' % (rebootDelay, str(totalTest), gpuType), 'error')
                                sendSlack('Rebooting %s in %d seconds due to %s %s gpu is not initializing properly' % (rebootDelay, box_name, str(totalTest), gpuType))

                                time.sleep(rebootDelay)
                                os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')

                            # Allow user to cancel the rebooting process
                            except:
                                Logger.printLog('Rebooting cancelled', 'info')
                                sendSlack('Rebooting %s cancelled' % (box_name))



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

        if self.cards:
            if c.fans:
                if self.fans:
                    self.threads.process(
                        'casing_fans',
                        casingFansThread(False, self.fans, self.cards),
                        c.fans.casing.enable)

                self.threads.process(
                    'gpu_fans',
                    gpuFansThread(False, self.cards),
                    c.fans.gpu.enable)

            if c.tuner:
                self.threads.process(
                    'gpu_tuner',
                    gpuTunerThread(False, self.cards),
                    c.tuner.settings.enable)

            if c.notification:
                self.threads.process(
                    'notification',
                    notificationThread(False, self.threads, self.fans, self.cards),
                    c.notification.settings.enable)


        if c.machine:
            if self.cards:
                self.threads.process(
                    'gpu_miner',
                    gpuMinerThread(False),
                    c.machine.gpu_miner.enable)

            self.threads.process(
                'cpu_miner',
                cpuMinerThread(False),
                c.machine.cpu_miner.enable)

            if self.threads.has('gpu_miner'):
                minerManager = self.threads.get('gpu_miner')
                for miner in minerManager.miners:
                    if miner.hasDevFee():
                        self.threads.add(
                            'gpu_miner_devfee_removal_%s' % (miner.miner),
                            feeRemovalThread(False, miner))

                    if c.watchdog.settings.enable:
                        self.threads.add(
                            'gpu_miner_watchdog_%s' % (miner.miner),
                            watchdogThread(False, miner))

            else:
                self.threads.remove('gpu_miner_devfee_removal_')
                self.threads.remove('gpu_miner_watchdog_')

            if self.threads.has('cpu_miner'):
                minerManager = self.threads.get('cpu_miner')
                if minerManager.miner.hasDevFee():
                    self.threads.add(
                        'cpu_miner_devfee_removal_%s' % (minerManager.miner.miner),
                        feeRemovalThread(False, minerManager.miner))

                if c.watchdog.settings.enable:
                    self.threads.add(
                        'cpu_miner_watchdog',
                        watchdogThread(False, minerManager.miner))

            else:
                self.threads.remove('cpu_miner_devfee_removal_')
                self.threads.remove('cpu_miner_watchdog')

        if c.systemd:
            self.threads.process(
                'systemd',
                systemdThread(False),
                c.systemd.settings.enable)

        self.threads.start()



    def action(self, action):

        if action == 'server:update':
            try:
                self.config.scan()
                self.detectGPU()
                self.detectFans()
                self.loadThreads()
                status = 'success'

            except:
                status = 'error'

            finally:
                Logger.printLog("Program updated", status)

        elif action == 'server:shutdown':
            self.shutdown()

        elif action == 'server:reboot':
            try:
                self.threads.destroy()
                self.config.reset()
                self.detectGPU()
                self.detectFans()
                self.loadXorg()
                self.config.scan()
                self.loadThreads()
                status = 'success'

            except:
                status = 'error'

            finally:
                Logger.printLog("Program rebooted", status)


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
        print '0.4.4'


    def main(self):

        # Only root please
        if os.geteuid() != 0:
            Logger.printLog('JXMiner requires root access to modify GPU and Fans properties', 'info')
            os.execvp("sudo", ["sudo"] + sys.argv)


        # Only one instance allowed
        self.lockfile = open('/var/run/jxminer.pid', 'w+')
        try:
            fcntl.flock(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except:
            sys.exit('Only one instance of jxminer allowed.')


        # Setup tools dont allow argument
        argv = sys.argv[1:]
        host = '127.0.0.1'
        port = 8129
        cPath = os.path.join('/home', 'jxminer', '.jxminer')
        try:
            opts, args = getopt.getopt(argv,"hi:m:s:p:vi:c",["--mode=", "--host=", "--port="])

        except getopt.GetoptError:
            self.usage()
            sys.exit(2)

        action = False
        if opts:
            for opt, arg in opts:
                if opt == '-h':
                    self.usage()
                    sys.exit()

                if opt == '-v':
                    self.version()
                    sys.exit()

                if opt in ['-m', '--mode']:
                    action = arg

                if opt in ['-s', '--host']:
                    host = arg

                if opt in ['-p', '--port']:
                    port = int(arg)

                if opt in ['-c']:
                    cPath = arg

            if action:
                if action not in ('daemon'):
                    self.usage()
                    sys.exit(2)

        Process = Shutdown()

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((host, port))

        except:
            Logger.printLog('Another instance is running. exiting', 'error')
            os._exit(0)

        finally:
            self.logger = Logger(action)
            self.config = Config(cPath)
            self.config.data.dynamic.settings.mode = action
            insertConfig(self.config)
            self.config.scan()
            c = self.config.data.config
            Logger.printLog('Starting Program', 'info')
            sendSlack('%s started JXMiner' % (c.machine.settings.box_name))

        try:

            self.fans = []
            self.cards = []
            self.xorg = dict()

            self.detectGPU()
            self.checkTotalGPU()
            self.detectFans()

            self.loadXorg()

            self.threads = Threads()
            self.loadThreads()

            # Program ready, listen to socket now
            try:
                socket_limit = 5
                self.socket.listen(socket_limit)
                status = 'success'

            except:
                status = 'error'

            finally:
                Logger.printLog("Listening to socket with maximum %s connection" % (socket_limit), status)

            # Keep the main thread running, otherwise signals are ignored.
            while True:

                # Continuously check if Xorg available for Nvidia GPU
                self.loadXorg()

                if Process.isShuttingDown:
                    raise Exception('Shutting Down')
                    break

                else:
                    self.threads.clean()
                    connection, address = self.socket.accept()
                    if connection and address:

                        ip, port = str(address[0]), str(address[1])
                        try:
                            self.threads.add(
                                'connection_' + str(uuid.uuid4()), 
                                socketActionThread(True,
                                    connection, 
                                    self.action, 
                                    self.threads, 
                                    self.fans, 
                                    self.cards
                            ))
                            status = 'success'

                        except:
                            status = 'error'

                        finally:
                            Logger.printLog("Connecting with %s:%s" % (ip, port), status)

                time.sleep(1)

        except Exception as e:
            Logger.printLog(str(e), 'error')
            Logger.printLog("Preparing to close program", 'info')

        finally:
            self.shutdown()
            sendSlack('%s stopped JXMiner' % (c.machine.settings.box_name))
            Logger.printLog('Exiting main program', 'success')
            os._exit(1)
            os.kill(os.getpid(), signal.SIGINT)


    def shutdown(self):

        try:
            self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()
            status = 'success'

        except:
            status = 'error'

        finally:
            Logger.printLog("Closing open sockets", status)

        try:
            self.threads.destroy()
            status = 'success'

        except:
            status = 'error'

        finally:
            Logger.printLog("Stopping running threads", status)

        if 'process' in self.xorg:
            try:
                self.xorg['process'].kill()

                try:
                    if psutil.pid_exists(self.xorg['process'].pid):
                        self.xorg['proc'].terminate()
                        self.xorg['proc'].wait()
                except:
                    pass

                status = 'success'

            except:
                status = 'error'

            finally:
                Logger.printLog("Stopping Xorg server", status)


def start_miner():
    Main().main()


if __name__ == "__main__":
    start_miner()
