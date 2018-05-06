#!/usr/bin/env python
#####
# Main Miner Controller
# Todo :
# 1. Implements Curve method for setting up GPU Fans and Casing Fans against temperature
# 2. Add ability to change configuration on the fly
# 4. Different configuration for each of the GPU that falls back into global one
# 5. Add ability to get GPU and fans data on the fly so other script can reference to this
# 7. GUI / TUI reporting for GPU, Fans and Miner?
# 14. Create exit script that reset all the GPU and Fans default automated settings upon script exits
# 15. Create installation scripts
#####

from modules.pynvml import *
from modules.rocmsmi import *
from modules.sysfs import *
from modules.utility import printLog

from entities.nvidia import Nvidia
from entities.amd import AMD
from entities.fan import Fan
from entities.threads import *

from threads.monitorCasingFans import *
from threads.monitorGpuFans import *
from threads.monitorGpuTuner import *
from threads.monitorSocketAction import *
from threads.monitorGpuMiner import *
from threads.monitorCpuMiner import *

from pprint import pprint

import os, sys, traceback, ConfigParser, socket, uuid


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
        printLog('No NVidia GPU found in the system', 'info')

    try:
        devices = listDevices()
        Config['server'].set('GPU', 'amd', str(len(devices)))
        if not devices:
            raise

        for i in devices:
            printLog('Initialized AMD GPU %s' % (i), 'success')
            GPUUnits.append(AMD(i))

    except:
        printLog('No AMD GPU found in the system', 'info')



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
                if Config['fans'].getboolean('casing', 'enable'):
                    if not JobThreads.has('casing_fans'):
                        try:
                            JobThreads.add('casing_fans', MonitorCasingFans(True, Config, FanUnits, GPUUnits))
                            status = 'success'
                        except:
                            status = 'error'
                        finally:
                            printLog('Starting Casing fan manager started', status)
                else:
                    if JobThreads.has('casing_fans'):
                        try:
                            JobThreads.remove('casing_fans')
                            status='success'
                        except:
                            status = 'error'
                        finally:
                            printLog('Stopping Casing fan manager', status)


            if Config['fans'].getboolean('gpu', 'enable'):
                if not JobThreads.has('gpu_fans'):
                    try:
                        JobThreads.add('gpu_fans', MonitorGPUFans(True, Config, GPUUnits))
                        status = 'success'
                    except:
                        status = 'error'
                    finally:
                        printLog('Starting GPU fan manager', status)

            else:
                if JobThreads.has('gpu_fans'):
                    try:
                        JobThreads.remove('gpu_fans')
                        status = 'success'
                    except:
                        status = 'error'
                    finally:
                        printLog('GPU fan manager stopped', 'success')


        if 'tuner' in Config:
            if Config['tuner'].getboolean('settings', 'enable'):
                if not JobThreads.has('gpu_tuner'):
                    try:
                        JobThreads.add('gpu_tuner', MonitorGPUTuner(True, Config, GPUUnits))
                        status = 'success'
                    except:
                        status = 'error'
                    finally:
                        printLog('Starting GPU tuner manager', status)

            else:
                if JobThreads.has('gpu_tuner'):
                    try:
                        JobThreads.remove('gpu_tuner')
                        status = 'success'
                    except:
                        status = 'error'
                    finally:
                        printLog('Stopping GPU tuner manager', status)



    if 'machine' in Config:
        if Config['machine'].getboolean('gpu_miner', 'enable'):
            if not JobThreads.has('gpu_miner'):
                try:
                    JobThreads.add('gpu_miner', MonitorGPUMiner(True, Config))
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog('Starting GPU miner manager', status)

        else:
            if JobThreads.has('gpu_miner'):
                try:
                    JobThreads.remove('gpu_miner')
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog('Stopping GPU miner manager', status)

        if Config['machine'].getboolean('cpu_miner', 'enable'):
            if not JobThreads.has('cpu_miner'):
                try:
                    JobThreads.add('cpu_miner', MonitorCPUMiner(True, Config))
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog('Starting CPU miner manager', status)
        else:
            if JobThreads.has('cpu_miner'):
                try:
                    JobThreads.remove('cpu_miner')
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog('Stopping CPU miner manager', status)




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

    data = []
    if action == 'update':
        try:
            loadConfig()
            loadThreads()
            data = Config
            status = 'success'
        except:
            status = 'error'
        finally:
            printLog("Updating program", status)

    elif action == 'gpuInfo':
        data = GPUUnits

    elif action == 'fansInfo':
        data = FanUnits

    elif action == 'shutdown':
        shutdown()

    elif action == 'reboot':
        try:
            JobThreads.destroy()
            loadConfig()
            loadThreads()
            status = 'success'

        except:
            status = 'error'

        finally:
            printLog("Rebooting program", status)

    return data


def main():

    global FanUnits
    global GPUUnits
    global JobThreads
    global Socket
    global Config
    global ConfigPath
    global XorgProcess

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
        printLog('Starting Program', 'info')
        Config = dict()
        ConfigPath = os.path.join(os.path.dirname(__file__), 'data')
        loadConfig()

    try:
        FanUnits = []
        GPUUnits = []

        XorgProcess = dict()

        detectGPU()
        detectFans()

        JobThreads = Threads()
        loadThreads()

        # Program ready, listen to socket now
        try:
            socketlimit = 5
            Socket.listen(socketlimit)
            status = 'success'
        except:
            status = 'error'
        finally:
            printLog("Listening to socket with maximum %s connection" % (socketlimit), status)

        # Keep the main thread running, otherwise signals are ignored.
        while True:

            # Clean Zombies
            try:
                JobThreads.clean()
                status = 'success'
            except:
                status = 'error'
            finally:
                printLog("Cleaning zombie threads", status)

            connection, address = Socket.accept()
            if connection and address:
                ip, port = str(address[0]), str(address[1])
                try:
                    JobThreads.add('actions-' + str(uuid.uuid4()), MonitorSocketAction(True, Config, connection, processAction, JobThreads, FanUnits, GPUUnits))
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog("Connecting with %s:%s" % (ip, port), status)

            time.sleep(1)

    except:
        shutdown()

    finally:
        printLog('Exiting main program', 'success')


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
        JobThreads.clean()
        status = 'success'
    except:
        status = 'error'
    finally:
        printLog("Closing open threads", status)

    if 'process' in XorgProcess:
        try:
            XorgProcess['process'].kill()
            XorgProcess['process'].wait

            if psutil.pid_exists(XorgProcess['process'].pid):
                XorgProcess['proc'].terminate()
                XorgProcess['proc'].wait()

            status = 'success'

        except:
            status = 'error'
        finally:
            printLog("Stopping Xorg server", status)


    sys.exit(0)

if __name__ == "__main__":
    main()
