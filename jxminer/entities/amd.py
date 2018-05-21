import time

from modules.rocmsmi import *
from gpu import GPU

class AMD(GPU):

    """
        This is a class for GPU Type AMD

        Core Level Tuning
        - AMDGPUPRO Linux kernel driver is limited to selecting core level per level only, one need to modify and
          flash the GPU bios to fine tune the core frequency and its watt usage

        Memory Level Tuning
        - This is not supported by this class, one need to flash the bios to change memory frequency and its
          watt usage

        Power Level Tuning
        - This is not supported yet by this class

        Fan Level Tuning
        - AMDGPUPRO Linux kernel driver will use 0 - 255 as the value for fan speed, while this class expect
          percentage based from 0 - 100 and will convert the percentage value to the linux kernel value

    """

    def init(self):
        self.type = 'AMD'
        self.strictPowerMode = False
        self.coreLevel = 100
        self.memoryLevel = False
        self.powerLevel = False
        self.fanSpeed = 0
        self.wattUsage = 0
        self.supportLevels = True
        self.machineIndex = 'card%s' % (self.index)

        try:
            setPerformanceLevel([self.machineIndex], 'manual')
        except:
            pass

        try:
            self.maxCoreLevel = getMaxLevel(self.machineIndex, 'gpu')
        except:
            self.maxCoreLevel = False
            self.supportLevels = False

        self.detect()


    def detect(self):
        self.temperature = getSysfsValue(self.machineIndex, 'temp')

        try:
            self.fanSpeed = self.round(int(getSysfsValue(self.machineIndex, 'fan')) / 2.55)
        except:
            self.fanSpeed = 0

        if self.supportLevels:
            self.wattUsage = parseSysfsValue('power', getSysfsValue(self.machineIndex, 'power'))


    def reset(self):
        resetFans([self.machineIndex])
        if self.supportLevels:
            resetClocks([self.machineIndex])


    def tune(self, **kwargs):
        if kwargs.get('fan', False):
            speed = self.round(kwargs.get('fan'))
            if speed != self.fanSpeed:
                setFanSpeed([self.machineIndex], self.round(speed * 2.55))
                self.fanSpeed = speed

        if self.supportLevels:
            if kwargs.get('core', False):
                level = self.round(kwargs.get('core'))
                if self.coreLevel != level:
                    self.coreLevel = level
                    self.setCoreLevel(level)


    def setCoreLevel(self, level):
        if self.supportLevels:
            levels = self.round((level * self.maxCoreLevel) / 100)
            if not self.strictPowerMode:
                levels = range(0, levels)
            else:
                levels = [ levels ]

            setClocks([self.machineIndex], 'gpu', levels)