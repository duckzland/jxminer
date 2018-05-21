import os
import argparse
import re
import sys
import subprocess
import json
from subprocess import check_output
import glob
import time
import collections

from pprint import pprint

# Version of the JSON output used to save clocks
JSON_VERSION = 1

# Set to 1 if an error occurs
RETCODE = 0

# Currently we have 5 values for PowerPlay Profiles
NUM_PROFILE_ARGS = 5

drmprefix = '/sys/class/drm'
hwmonprefix = '/sys/class/hwmon'
powerprefix = '/sys/kernel/debug/dri/'

valuePaths = {
    'id' : {'prefix' : drmprefix, 'filepath' : 'device', 'needsparse' : True},
    'vbios' : {'prefix' : drmprefix, 'filepath' : 'vbios_version', 'needsparse' : False},
    'perf' : {'prefix' : drmprefix, 'filepath' : 'power_dpm_force_performance_level', 'needsparse' : False},
    'sclk_od' : {'prefix' : drmprefix, 'filepath' : 'pp_sclk_od', 'needsparse' : False},
    'mclk_od' : {'prefix' : drmprefix, 'filepath' : 'pp_mclk_od', 'needsparse' : False},
    'sclk' : {'prefix' : drmprefix, 'filepath' : 'pp_dpm_sclk', 'needsparse' : False},
    'mclk' : {'prefix' : drmprefix, 'filepath' : 'pp_dpm_mclk', 'needsparse' : False},
    'profile' : {'prefix' : drmprefix, 'filepath' : 'pp_compute_power_profile', 'needsparse' : False},
    'fan' : {'prefix' : hwmonprefix, 'filepath' : 'pwm1', 'needsparse' : False},
    'fanmax' : {'prefix' : hwmonprefix, 'filepath' : 'pwm1_max', 'needsparse' : False},
    'fanpwm' : {'prefix' : hwmonprefix, 'filepath' : 'pwm1_enable', 'needsparse' : False},
    'temp' : {'prefix' : hwmonprefix, 'filepath' : 'temp1_input', 'needsparse' : True},
    'power' : {'prefix' : powerprefix, 'filepath' : 'amdgpu_pm_info', 'needsparse' : True}
}


def getSysfsValue(device, key):

    pathDict = valuePaths[key]
    fileValue = ''
    filePath = os.path.join(pathDict['prefix'], device, 'device', pathDict['filepath'])

    if pathDict['prefix'] == hwmonprefix:
        """ HW Monitor values have a different path structure """
        print getHwmonFromDevice(device)
        if not getHwmonFromDevice(device):
            return None
        filePath = os.path.join(getHwmonFromDevice(device), pathDict['filepath'])

    if pathDict['prefix'] == powerprefix:
        """ Power consumption is in debugfs and has a different path structure """
        filePath = os.path.join(powerprefix, device[4:], 'amdgpu_pm_info')

    if not os.path.isfile(filePath):
        return None

    with open(filePath, 'r') as fileContents:
        fileValue = fileContents.read().rstrip('\n')

    """ Some sysfs files aren't a single line of text """
    if pathDict['needsparse']:
        fileValue = parseSysfsValue(key, fileValue)

    if fileValue == '':
        raise AssertionError("Empty SysFS Value when parsing for %s:%s" % (device, key))

    return fileValue


def parseSysfsValue(key, value):

    if key == 'id':
        return value[2:]
    if key == 'temp':
        return int(value) / 1000
    if key == 'power':
        for line in value.splitlines():
            if 'average GPU' in line:
                return str.lstrip(line.replace(' W (average GPU)', ''))
    return ''


def parseDeviceNumber(deviceNum):
    return 'card' + str(deviceNum)


def parseDeviceName(deviceName):
    return deviceName[4:]


def doesDeviceExist(device):
    if os.path.exists(os.path.join(drmprefix, device)) == 0:
        return False
    return True


def writeToSysfs(fsFile, fsValue):
    if not os.path.isfile(fsFile):
        raise AssertionError('Cannot write to sysfs file. File does not exist')
        return False
    with open(fsFile, 'w') as fs:
        try:
            fs.write(str(fsValue) + '\n')
        except OSError:
            print('Unable to write to sysfs file' + fsFile)
            return False
    return True


def listDevices():
    devicelist = []
    for device in os.listdir(drmprefix) :
       if re.match(r'^card\d+$', device) and len(glob.glob(os.path.join(drmprefix, device, 'device', 'driver', 'module', 'drivers', 'pci*amdgpu'))) != 0:
          devicelist.append(device)
    return sorted(devicelist)


def listAmdHwMons():
    hwmons = []
    for mon in os.listdir(hwmonprefix):
        tempname = os.path.join(hwmonprefix, mon, 'name')
        if os.path.isfile(tempname):
            with open(tempname, 'r') as tempmon:
                drivername = tempmon.read().rstrip('\n')
                if drivername in ['radeon', 'amdgpu']:
                    hwmons.append(os.path.join(hwmonprefix, mon))
    return hwmons


def getHwmonFromDevice(device):
    drmdev = os.path.realpath(os.path.join(drmprefix, device, 'device'))
    for hwmon in listAmdHwMons():
        if os.path.realpath(os.path.join(hwmon, 'device')) == drmdev:
            return hwmon
    return None


def getFanSpeed(device):
    fanLevel = getSysfsValue(device, 'fan')
    fanMax = getSysfsValue(device, 'fanmax')
    if not fanLevel or not fanMax:
        return 0
    return round((int(fanLevel) / int(fanMax)) * 100, 2)


def getCurrentClock(device, clock, type):
    currClk = ''

    currClocks = getSysfsValue(device, 'sclk')
    if clock == 'mem':
        currClocks = getSysfsValue(device, 'mclk')

    if not currClocks:
        return None

    for line in currClocks.splitlines():
        if re.match(r'.*\*$', line):
            if (type == 'freq'):
                currClk = line[3:-2]
            else:
                currClk = line[0]
            break
    return currClk


def getMaxLevel(device, type):

    if type not in ['gpu', 'mem']:
        print 'Invalid level type' + type
        return ''

    key = 'sclk'
    if type == 'mem':
        key = 'mclk'

    levels = getSysfsValue(device, key)
    if not levels:
        return 0
    return int(levels.splitlines()[-1][0])


def findFile(prefix, file, device):
    pcPaths = glob.glob(os.path.join(prefix, '*', file))
    for path in pcPaths:
        if isCorrectPowerDevice(os.path.dirname(path), device):
            return path
    return ''


def setPerfLevel(device, level):
    validLevels = ['auto', 'low', 'high', 'manual']
    perfPath = os.path.join(drmprefix, device, 'device', 'power_dpm_force_performance_level')

    if level not in validLevels:
        return False

    if not os.path.isfile(perfPath):
        return False

    writeToSysfs(perfPath, level)
    return True


def setPerformanceLevel(deviceList, level):
    for device in deviceList:
        setPerfLevel(device, level)


def setClocks(deviceList, clktype, clk):
    if not clk:
        print 'Invalid clock frequency'
        return

    value = ''.join(map(str, clk))

    try:
        int(value)
    except ValueError:
        return

    for device in deviceList:
        if not isPowerplayEnabled(device):
            continue

        devpath = os.path.join(drmprefix, device, 'device')
        if clktype == 'gpu':
            clkFile = os.path.join(devpath, 'pp_dpm_sclk')
        else:
            clkFile = os.path.join(devpath, 'pp_dpm_mclk')

        if any(int(item) > getMaxLevel(device, clktype) for item in clk):
            continue

        setPerfLevel(device, 'manual')
        writeToSysfs(clkFile, value)


def setClockOverDrive(deviceList, clktype, value, autoRespond):
    try:
        int(value)
    except ValueError:
        return

    confirmOverDrive(autoRespond)

    for device in deviceList:
        if not isPowerplayEnabled(device):
            continue

        devpath = os.path.join(drmprefix, device, 'device')
        if clktype == 'gpu':
            odPath = os.path.join(devpath, 'pp_sclk_od')
            name = 'GPU Clock'
        elif clktype == 'mem':
            odPath = os.path.join(devpath, 'pp_mclk_od')
            name = 'GPU Memory Clock'
        else:
            continue

        if int(value) < 0:
            return

        if int(value) > 20:
            value = '20'

        if (writeToSysfs(odPath, value)):
            setClocks([device], clktype, [getMaxLevel(device, clktype)])


def isPowerplayEnabled(device):
    if not doesDeviceExist(device) or os.path.isfile(os.path.join(drmprefix, device, 'device', 'power_dpm_force_performance_level')) == 0:
        return False
    return True


def resetFans(deviceList):
    for device in deviceList:
        if not isPowerplayEnabled(device):
            continue

        hwmon = getHwmonFromDevice(device)
        if not hwmon:
            continue

        fanpath = os.path.join(hwmon, 'pwm1_enable')
        writeToSysfs(fanpath, '2')


def setFanSpeed(deviceList, fan):
    for device in deviceList:
        if not isPowerplayEnabled(device):
            continue

        hwmon = getHwmonFromDevice(device)
        if not hwmon:
            continue

        fanpath = os.path.join(hwmon, 'pwm1_enable')
        writeToSysfs(fanpath, '1')

        fanpath = os.path.join(hwmon, 'pwm1')
        maxfan = getSysfsValue(device, 'fanmax')
        if not maxfan:
            continue

        if int(fan) > int(maxfan):
            continue

        writeToSysfs(fanpath, str(fan))


def setProfile(deviceList, profile):
    for device in deviceList:
        setPerfLevel(device, 'auto')
        writeProfileSysfs(device, profile)


def resetProfile(deviceList):
    for device in deviceList:
        setPerfLevel(device, 'auto')
        writeProfileSysfs(device, 'reset')


def resetOverDrive(deviceList):
    for device in deviceList:
        devpath = os.path.join(drmprefix, device, 'device')
        for type, name in zip(['sclk', 'mclk'], ['Clock', 'Memory Clock']):
            odpath = os.path.join(devpath, 'pp_%s_od' % type)
            if not os.path.isfile(odpath):
                continue
            od = getSysfsValue(device, '%s_od' % type)
            if not od or int(od) != 0:
                writeToSysfs(odpath, '0')


def resetClocks(deviceList):
    for device in deviceList:
        resetOverDrive([device])
        setPerfLevel(device, 'auto')

        odgpu = getSysfsValue(device, 'sclk_od')
        odmem = getSysfsValue(device, 'mclk_od')
        perf = getSysfsValue(device, 'perf')
