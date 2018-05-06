import sys, subprocess, os, time, signal
sys.path.append('../')
from modules.pynvml import *
from gpu import GPU

class Nvidia(GPU):

    """
        This is a class for GPU Type Nvidia

        Fan Level Tuning
        - Fan level will use number from 0 (turned off) up to 100 (full speed) to manage fan speed

        Power Level Tuning
        - The power level will use number from 0 - 100 which equal to x multiplied by maximum watt allowed by card

        Core Level Tuning
        - The core level tuning will use number from 0 - 100, 0 will be equal to -200 core clock, 50 will be equal
          to no core modification and 100 will be equal to +200 core clock

        Memory Level Tuning
        - The memory level tuning will use number from 0 - 100, 0 will be equal to -2000 memory clock, 50 will be equal
          to no memory modification and 100 will be equal to +2000 memory clock

        LED Brightness
        - Value from 0 (turned off) to 100 (full brightness)
    """

    fanControlState = 'automatic'

    def init(self):
        nvmlInit()
        self.handle = nvmlDeviceGetHandleByIndex(self.index)
        self.type = 'Nvidia'
        self.maxCoreClockLevel = nvmlDeviceGetMaxClockInfo(self.handle, NVML_CLOCK_GRAPHICS)
        self.maxMemoryClockLevel = nvmlDeviceGetMaxClockInfo(self.handle, NVML_CLOCK_MEM)
        self.maxPowerWattLevel = nvmlDeviceGetPowerManagementDefaultLimit(self.handle)
        if 'manual' not in Nvidia.fanControlState:
            Nvidia.fanControlState = 'manual'
            p = self.call(['nvidia-settings', '-a', 'GPUFanControlState=%s' % ('1')], {'DISPLAY': ':0'})
            p.wait()
        self.setLEDBrightness(0)

        self.coreLevel = 100
        self.memoryLevel = 100
        self.powerLevel = 100
        self.wattUsage = 0
        self.detect()


    def detect(self):
        self.temperature = nvmlDeviceGetTemperature(self.handle, 0)
        self.fanSpeed = nvmlDeviceGetFanSpeed(self.handle)
        self.wattUsage = '%.2f' % (float(nvmlDeviceGetPowerUsage(self.handle)) / 1000)


    def tune(self, **kwargs):
        if kwargs.get('fan', False):
            speed = self.round(kwargs.get('fan'))
            if speed != self.fanSpeed:
                self.setFanSpeed(speed)
                self.fanSpeed = speed

        if kwargs.get('core', False):
            level = self.round(kwargs.get('core'))
            if self.coreLevel != level:
                self.setCoreLevel(level)
                self.coreLevel = level

        if kwargs.get('power', False):
           level = self.round(kwargs.get('power'))
           if self.powerLevel != level:
                self.setPowerLevel(level)
                self.powerLevel = level

        if kwargs.get('memory', False):
           level = self.round(kwargs.get('memory'))
           if self.memoryLevel != level:
                self.setMemoryLevel(level)
                self.memoryLevel = level


    def reset(self):
        self.setCoreLevel(50)
        self.setLEDBrightness(100)

        if Nvidia.fanControlState != 'automatic':
            Nvidia.fanControlState = 'automatic'
            p = self.call(['nvidia-settings', '-a', 'GPUFanControlState=%s' % ('0')], {'DISPLAY': ':0'})
            p.wait()

        nvmlShutdown()


    def setLEDBrightness(self, state):
        self.brightness = state
        p = self.call(['nvidia-settings', '-a', '[gpu:%s]/GPULogoBrightness=%s' % (self.index, self.brightness)], {'DISPLAY': ':0'})
        p.wait()


    def setFanSpeed(self, speed):
        p = self.call(['nvidia-settings', '-a', '[fan:%s]/GPUTargetFanSpeed=%s' % (self.index, max(min(100, speed), 0))], {'DISPLAY': ':0'})
        p.wait()


    def setCoreLevel(self, level):
        # Nvidia settings range for offset is between -200 up to +200
        clock = max(min(200, self.round((level * 4) - 200)), -200)
        if clock > 0:
            clock = '+' + str(clock)
        p = self.call(['nvidia-settings', '-a', '[gpu:%s]/GPUGraphicsClockOffset[3]=%s' % (self.index, max(min(200, self.round((level * 4) - 200)), -200))], {'DISPLAY': ':0'})
        p.wait()


    def setMemoryLevel(self, level):
        # Nvidia settings range for offset is between -2000 up to +2000
        p = self.call(['nvidia-settings', '-a', '[gpu:%s]/GPUMemoryTransferRateOffset[3]=%s' % (self.index, max(min(2000, self.round((level * 40) - 2000)), -2000))], {'DISPLAY': ':0'})
        p.wait()


    def setPowerLevel(self, level):
        # Limit the power level between 50% up to 100% of maximum power watt level (varies in different card model)
        nvmlDeviceSetPowerManagementLimit(self.handle, max(min(self.maxPowerWattLevel, self.round(level * (self.maxPowerWattLevel / 100))), self.maxPowerWattLevel / 2))