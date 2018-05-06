#!/usr/bin/env python

from entities.shutdown import *
from entities.nvidia import Nvidia
from entities.amd import AMD
from entities.fan import Fan
from entities.threads import *

from modules.transfer import *
from modules.utility import printLog

from threads.monitorCasingFans import *
from threads.monitorGpuFans import *
from threads.monitorGpuTuner import *
from threads.monitorSocketAction import *
from threads.monitorGpuMiner import *
from threads.monitorCpuMiner import *


import ConfigParser, io, sys, getopt, pickle, socket, signal
from pprint import pprint

def usage():
    print 'client.py -a <refresh|get_gpu|get_fans> -f <json|line>'

def main(argv):
    action = ''
    format = ''

    try:
        opts, args = getopt.getopt(argv,"hi:a:f:",["--action=","--format="])

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()

        elif opt in ("-a", "--action"):
            action = arg

        elif opt in ("-f", "--format"):
            format = arg

    if not action:
        usage()
        sys.exit(2)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        host = "127.0.0.1"
        port = 8129
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((host, port))
        printLog('Connected to --#%s#-:--#%s#-' % (host, port))
    except:
        printLog("Connection error")
        sys.exit()

    try:
        t = Transfer(soc)
        t.send(action)
        printLog('Sending --#%s#- action' % (action))

        if action in ('gpuInfo', 'fansInfo'):
            data = t.recv()
            printLog('Receiving data')
            data_variable = pickle.loads(data);

        elif 'monitor' in action:
            monitor(t)

        elif action in ('cpuMiningInfo', 'gpuMiningInfo'):
            pass


    except ServiceExit:
        printLog('Closing --#%s#- action' % (action))
        t.send('close')
        t.wait()

    finally:
        soc.close()
        print('Exiting client program')
        sys.exit()


def shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise ServiceExit


def monitor(t):
    while True:
        line = t.recv()
        if not line:
            break
        print(line.strip('\n'))


if __name__ == "__main__":
    main(sys.argv[1:])
