import time

from modules.rocmsmi import *
from entities.gpu import GPU

class AMD(GPU):

    """
        This is a class for GPU Type AMD

        Core Level Tuning
        - AMDGPUPRO Linux kernel driver is limited to selecting core level per level only, one need to modify and
          flash the GPU bios to fine tune the core frequency and its watt usage

        Memory Level Tuning
        - AMDGPUPRO Linux kernel driver is limited to selecting memory level per level only. It might not be useful
          to change memory level since mining operation usually will need to have the highest memory clocks available

        Power Level Tuning
        - Newer AMDGPUPRO Linux kernel allows user to define custom power caps to limit the maximum power that
          the gpu can draw. The value is from 0 - 100%, which will converted to the watt based on card maximum
          power draw and card minimum power draw set in the card vbios.

        Fan Level Tuning
        - AMDGPUPRO Linux kernel driver will use 0 - 255 as the value for fan speed, while this class expect
          percentage based from 0 - 100 and will convert the percentage value to the linux kernel value

    """

    def init(self):

        self.type = 'AMD'
        self.strictMode = False
        self.coreLevel = 100
        self.memoryLevel = 100
        self.powerLevel = 100
        self.fanLevel = False
        self.fanSpeed = 0
        self.wattUsage = 0
        self.supportLevels = False
        self.machineIndex = 'card%s' % (self.index)

        if (setPerfLevel(self.machineIndex, 'manual')):
            self.maxCoreLevel = getMaxLevel(self.machineIndex, 'gpu')
            self.maxMemoryLevel = getMaxLevel(self.machineIndex, 'mem')
            self.maxPowerLevel = getPowerCapMax(self.machineIndex)
            self.supportLevels = int(self.maxCoreLevel) + int(self.maxMemoryLevel) > 0;

        self.detect()



    def detect(self):
        self.temperature = getSysfsValue(self.machineIndex, 'temp')
        self.fanSpeed = self.round(int(getSysfsValue(self.machineIndex, 'fan')) / 2.55)

        if self.fanLevel == False:
            self.fanLevel = self.fanSpeed

        if self.supportLevels:
            self.wattUsage = getSysfsValue(self.machineIndex, 'power')



    def reset(self):
        resetFans([self.machineIndex])
        if self.supportLevels:
            resetClocks([self.machineIndex])



    def setFanLevel(self, level):
        if level != self.fanSpeed:
            setFanSpeed([self.machineIndex], self.round(level * 2.55))
            self.fanSpeed = level
            self.fanLevel = level



    def setCoreLevel(self, level):
        if self.supportLevels and self.isNotAtLevel('core', level):
            s = self.strictMode
            m = self.maxCoreLevel
            d = self.round((level / (100 / (m + 1))))
            x = 0 if d < 0 else m if d > m else d
            levels = [ x ] if s else range(0, x)
            setClocks([self.machineIndex], 'gpu', levels)
            self.coreLevel = level



    def setMemoryLevel(self, level):
        if self.supportLevels and self.isNotAtLevel('memory', level):
            s = self.strictMode
            m = self.maxMemoryLevel
            d = self.round( (level / (100 / (m + 1))))
            x = 0 if d < 0 else m if d > m else d
            levels = [ x ] if s else range(1, x)
            setClocks([self.machineIndex], 'mem', levels)
            self.memoryLevel = level



    def setPowerLevel(self, level):
        if self.supportLevels and self.isNotAtLevel('power', level):
            setPowerCap(self.machineIndex, int(level) * int(self.maxPowerLevel) / int(100))
            self.powerLevel = level
