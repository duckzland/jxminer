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
        - AMDGPUPRO Linux kernel driver is limited to selecting memory level per level only. It might not be useful
          to change memory level since mining operation usually will need to have the highest memory clocks available

        Power Level Tuning
        - This is not supported yet by this class

        Fan Level Tuning
        - AMDGPUPRO Linux kernel driver will use 0 - 255 as the value for fan speed, while this class expect
          percentage based from 0 - 100 and will convert the percentage value to the linux kernel value

    """

    def init(self):
        self.type = 'AMD'
        self.strictPowerMode = False
        self.strictMemoryMode = False
        self.coreLevel = 100
        self.memoryLevel = False
        self.powerLevel = False
        self.fanLevel = False
        self.fanSpeed = 0
        self.wattUsage = 0
        self.supportLevels = True
        self.machineIndex = 'card%s' % (self.index)

        setPerformanceLevel([self.machineIndex], 'manual')
        self.maxCoreLevel = getMaxLevel(self.machineIndex, 'gpu')
        self.maxMemoryLevel = getMaxLevel(self.machineIndex, 'mem')
        self.detect()


    def detect(self):
        self.temperature = getSysfsValue(self.machineIndex, 'temp')

        try:
            self.fanSpeed = self.round(int(getSysfsValue(self.machineIndex, 'fan')) / 2.55)
        except:
            self.fanSpeed = 0

        if self.fanLevel == False:
            self.fanLevel = self.fanSpeed

        if self.supportLevels:
            self.wattUsage = getSysfsValue(self.machineIndex, 'power')


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
                self.fanLevel = speed

        if self.supportLevels:
            if kwargs.get('core', False):
                level = self.round(kwargs.get('core'))
                if self.coreLevel != level:
                    self.coreLevel = level
                    self.setCoreLevel(level)

            if kwargs.get('memory', False):
                level = self.round(kwargs.get('memory'))
                if self.memoryLevel != level:
                    self.memoryLevel = level
                    self.setMemoryLevel(level)

            # Extend this to lower / increase power using power play?
            if kwargs.get('power', False):
                pass


    def setCoreLevel(self, level):
        if self.supportLevels:
            levels = self.round((level * self.maxCoreLevel) / 100)
            if not self.strictPowerMode:
                # Driver < 4.30 wants to allow level
                levels = range(0, levels)

                # Driver > 4.30 wants to mask level instead.
                #if levels == self.maxCoreLevel:
                #    levels = []
                #else:
                #    levels = range(levels + 1, self.maxCoreLevel)

            else:
                levels = [ levels ]

            setClocks([self.machineIndex], 'gpu', levels)



    def setMemoryLevel(self, level):
        if self.supportLevels:
            levels = self.round((level * self.maxMemoryLevel) / 100)
            if not self.strictMemoryMode:
                # Driver < 4.30 wants to allow level
                levels = range(0, levels)

                # Driver > 4.30 wants to mask level instead.
                #if levels == self.maxMemoryLevel:
                #    levels = []
                #else:
                #    levels = range(levels + 1, self.maxMemoryLevel)
            else:
                levels = [ levels ]

            setClocks([self.machineIndex], 'mem', levels)


    # Extend this to lower / increase power using power play?
    def setPowerLevel(self, level):
        pass