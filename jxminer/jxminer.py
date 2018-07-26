#!/usr/bin/env python
#####
# Main Miner Controller
# Todo :
# 1. Split Config into separate Class
# 2. Split PrintLog into separate Class
#
#####

import os, sys, traceback, ConfigParser, socket, uuid, getopt, signal, time

# Registering main root path for sane building!
sys.path.append(os.path.dirname(__file__))

from modules.pynvml import *
from modules.rocmsmi import *
from modules.sysfs import *
from modules.utility import printLog, sendSlack

from entities.nvidia import Nvidia
from entities.amd import AMD
from entities.fan import Fan
from entities.threads import *
from entities.shutdown import Shutdown

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

def detectGPU():

    global Config
    global XorgProcess

    Config['server'].add_section('GPU')

    try:
        nvmlInit()
        deviceCount = nvmlDeviceGetCount()
        Config['server'].set('GPU', 'nvidia', str(deviceCount))
        loadXorg()
        for i in range(deviceCount):
            printLog('Initialized NVidia GPU %s' % (i), 'success')
            GPUUnits.append(Nvidia(i))

    except NVMLError:
        Config['server'].set('GPU', 'nvidia', '0')
        printLog('No NVidia GPU found in the system', 'info')

    try:
        devices = listDevices()
        Config['server'].set('GPU', 'amd', str(len(devices)))
        if not devices:
            raise

        for i in devices:
            index = i.replace('card', '')
            printLog('Initialized AMD GPU %s' % (index), 'success')
            GPUUnits.append(AMD(index))

    except:
        Config['server'].set('GPU', 'amd', '0')
        printLog('No AMD GPU found in the system', 'info')



def checkTotalGPU():
    global Config

    if Config['machine'].has_section('gpu_check_total') and Config['machine'].getboolean('gpu_check_total', 'enable'):
        for gpuType in ['amd', 'nvidia']:
            limit = Config['machine'].getint('gpu_check_total', gpuType)
            detected = Config['server'].getint('GPU', gpuType)
            totalTest = limit - detected
            box_name = Config['machine'].get('settings', 'box_name')

            if limit > 0:
                if totalTest == 0:
                    printLog('%s %s gpu initialized properly' % (str(detected), gpuType), 'success')
                    sendSlack('%s %s gpu initialized properly at %s' % (str(detected), gpuType, box_name))

                else:
                    printLog('%s %s gpu failed to initialize' % (str(totalTest), gpuType), 'error')
                    sendSlack('%s %s gpu failed to initialize at %s' % (str(totalTest), gpuType, box_name))

                    if Config['machine'].getboolean('gpu_check_total', 'reboot_when_failed'):
                        printLog('Rebooting due to %s %s gpu is not initializing properly' % (str(totalTest), gpuType), 'error')
                        sendSlack('Rebooting %s due to %s %s gpu is not initializing properly' % (box_name, str(totalTest), gpuType))
                        time.sleep(30)
                        os.system('echo 1 > /proc/sys/kernel/sysrq && echo b > /proc/sysrq-trigger')


def detectFans():

    blacklisted = Config['sensors'].options('blacklisted')
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
                    printLog('Initialized fan %s:%s:%s' % (type, sensor, device), 'success')
                    FanUnits.append(Fan(device, {
                        'speed': os.path.join(prefix, sensor, extra, '%s'),
                        'pwm': os.path.join(prefix, sensor, extra, '%s_enable'),
                    }))

    if len(FanUnits) == 0:
        printLog('No casing fan found', 'info')


def loadXorg():

    if 'process' in XorgProcess or Config['server'].getint('GPU', 'nvidia') < 1:
        return

    try:
        subprocess.check_output(['pidof', 'Xorg'])
        printLog('Xorg instance found', 'info')
    except:
        XorgProcess['process'] = subprocess.Popen(['X', ':0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        XorgProcess['process'].wait
        XorgProcess['proc'] = psutil.Process(XorgProcess['process'].pid)

        p = subprocess.Popen(['xrandr', '--setprovideroutputsource', 'modesetting NVIDIA-0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        p = subprocess.Popen(['xrandr', '--auto'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

        printLog('Loading and tuning Xorg server', 'success')



def loadThreads():

    global Config
    global JobThreads

    if GPUUnits:
        if 'fans' in Config:
            if FanUnits:
                JobThreads.process(
                    'casing_fans',
                    casingFansThread(False, Config, FanUnits, GPUUnits),
                    Config['fans'].getboolean('casing', 'enable'))

                JobThreads.process(
                    'gpu_fans',
                    gpuFansThread(False, Config, GPUUnits),
                    Config['fans'].getboolean('gpu', 'enable'))

        if 'tuner' in Config:
            JobThreads.process(
                'gpu_tuner',
                gpuTunerThread(False, Config, GPUUnits),
                Config['tuner'].getboolean('settings', 'enable'))

        if 'notification' in Config:
            JobThreads.process(
                'notification',
                notificationThread(False, Config, JobThreads, FanUnits, GPUUnits),
                Config['notification'].getboolean('settings', 'enable'))


    if 'machine' in Config:
        JobThreads.process(
            'gpu_miner',
            gpuMinerThread(False, Config),
            Config['machine'].getboolean('gpu_miner', 'enable'))

        JobThreads.process(
            'cpu_miner',
            cpuMinerThread(False, Config),
            Config['machine'].getboolean('cpu_miner', 'enable'))

        if JobThreads.has('gpu_miner'):
            minerManager = JobThreads.get('gpu_miner')
            for miner in minerManager.miners:
                if miner.hasDevFee():
                    JobThreads.add('gpu_miner_devfee_removal_%s' % (miner.miner), feeRemovalThread(False, miner))

                if 'watchdog' in Config and Config['watchdog'].getboolean('settings', 'enable'):
                    JobThreads.add('gpu_miner_watchdog_%s' % (miner.miner), watchdogThread(False, Config, miner))

        else:
            JobThreads.remove('gpu_miner_devfee_removal_')
            JobThreads.remove('gpu_miner_watchdog_')

        if JobThreads.has('cpu_miner'):
            minerManager = JobThreads.get('cpu_miner')
            if minerManager.miner.hasDevFee():
                JobThreads.add('cpu_miner_devfee_removal_%s' % (minerManager.miner.miner), feeRemovalThread(False, minerManager.miner))

            if 'watchdog' in Config and Config['watchdog'].getboolean('settings', 'enable'):
                JobThreads.add('cpu_miner_watchdog', watchdogThread(False, Config, minerManager.miner))

        else:
            JobThreads.remove('cpu_miner_devfee_removal_')
            JobThreads.remove('cpu_miner_watchdog')

    if 'systemd' in Config:
        JobThreads.process(
            'systemd',
            systemdThread(False, Config),
            Config['systemd'].getboolean('settings', 'enable'))

    JobThreads.start()



def loadConfig():

    global Config

    for type in os.listdir(ConfigPath):
        for file in os.listdir(os.path.join(ConfigPath, type)):
            if file.lower().endswith('.ini'):
                conf = ConfigParser.ConfigParser(allow_no_value=True)
                path = os.path.join(ConfigPath, type, file)
                name = file.lower().replace('.ini', '')

                localPath = os.path.join('/etc', 'jxminer', type, file)
                userPath = os.path.join('~/', '.jxminer', type, file)

                if os.path.isfile(userPath):
                    path = userPath

                elif os.path.isfile(localPath):
                    path = localPath

                try:
                    conf.read(path)
                    Config[name] = conf
                    status = 'success'

                except:
                    status = 'error'

                finally:
                    printLog('Loading %s configuration from %s' % (name, path), status)

    Config['server'] = ConfigParser.ConfigParser(allow_no_value=True)

    return Config


def processAction(action):

    global FanUnits
    global GPUUnits
    global Config
    global JobThreads

    if action == 'server:update':
        try:
            loadConfig()
            detectGPU()
            detectFans()
            loadThreads()
            status = 'success'

        except:
            status = 'error'

        finally:
            printLog("Program updated", status)

    elif action == 'server:shutdown':
        shutdown()

    elif action == 'server:reboot':
        try:
            JobThreads.destroy()
            loadConfig()
            loadThreads()
            status = 'success'

        except:
            status = 'error'

        finally:
            printLog("Program rebooted", status)


def usage():
    print 'jxminer -m|-h'
    print '   -m <mode>'
    print '      daemon         Run the program as daemon, logging will be minimized'
    print '   -h Prints this help message'
    print '   -v Prints the server version'


def version():
    print '0.3.21'


def main():

    global FanUnits
    global GPUUnits
    global JobThreads
    global Socket
    global Config
    global ConfigPath
    global XorgProcess

    if os.geteuid() != 0:
        printLog('JXMiner requires root access to modify GPU and Fans properties', 'info')
        os.execvp("sudo", ["sudo"] + sys.argv)

    # Setup tools dont allow argument
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv,"hi:m:vi",["--mode="])

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    action = False
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()

        if opt == '-v':
            version()
            sys.exit()

        if opt in ["-m", "--mode"]:
            action = arg

    if action:
        if action not in ('daemon'):
            usage()
            sys.exit(2)

    Process = Shutdown()

    try:
        host = '127.0.0.1'
        port = 8129
        Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        Socket.bind((host, port))

    except:
        printLog('Another instance is running. exiting', 'error')
        os._exit(0)

    finally:
        Config = dict()
        Config['dynamic'] = ConfigParser.ConfigParser(allow_no_value=True)
        Config['dynamic'].add_section('settings')
        Config['dynamic'].set('settings', 'mode', action)

        ConfigPath = os.path.join(os.path.dirname(__file__), 'data')
        loadConfig()

        printLog('Starting Program', 'info', True, True, Config)
        sendSlack(
            '%s started JXMiner' % (Config['machine'].get('settings', 'box_name')),
            Config['slack'].get('settings', 'token'),
            Config['slack'].get('settings', 'channel'),
            Config['slack'].get('settings', 'enable')
            )

    try:

        FanUnits = []
        GPUUnits = []
        XorgProcess = dict()

        detectGPU()
        checkTotalGPU()
        detectFans()

        loadXorg()

        JobThreads = Threads()
        loadThreads()

        # Program ready, listen to socket now
        try:
            socket_limit = 5
            Socket.listen(socket_limit)
            status = 'success'

        except:
            status = 'error'

        finally:
            printLog("Listening to socket with maximum %s connection" % (socket_limit), status)

        # Keep the main thread running, otherwise signals are ignored.
        while True:

            # Continuously check if Xorg available for Nvidia GPU
            loadXorg()

            if Process.isShuttingDown:
                raise Exception('Shutting Down')
                break

            else:

                JobThreads.clean()
                connection, address = Socket.accept()
                if connection and address:

                    ip, port = str(address[0]), str(address[1])
                    try:
                        JobThreads.add('connection_' + str(uuid.uuid4()), socketActionThread(True, Config, connection, processAction, JobThreads, FanUnits, GPUUnits))
                        status = 'success'

                    except:
                        status = 'error'

                    finally:
                        printLog("Connecting with %s:%s" % (ip, port), status)

            time.sleep(1)

    except:
        printLog("Preparing to close program", 'info')

    finally:
        shutdown()
        sendSlack('%s stopped JXMiner' % (Config['machine'].get('settings', 'box_name')))
        printLog('Exiting main program', 'success')
        os._exit(1)
        os.kill(os.getpid(), signal.SIGINT)


def shutdown():

    try:
        Socket.shutdown(socket.SHUT_WR)
        Socket.close()
        status = 'success'

    except:
        status = 'error'

    finally:
        printLog("Closing open sockets", status)

    try:
        JobThreads.destroy()
        status = 'success'

    except:
        status = 'error'

    finally:
        printLog("Stopping running threads", status)

    if 'process' in XorgProcess:
        try:
            XorgProcess['process'].kill()

            try:
                if psutil.pid_exists(XorgProcess['process'].pid):
                    XorgProcess['proc'].terminate()
                    XorgProcess['proc'].wait()
            except:
                pass

            status = 'success'

        except:
            status = 'error'

        finally:
            printLog("Stopping Xorg server", status)



if __name__ == "__main__":
    main()
