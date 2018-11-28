import os, subprocess, math

from modules.sysfs import *

class Fan:

    """
        This is a class for defining a single Fan instance
        Linux PWM will use numeric value from 0-255 for setting the fan level
        while this class expect percentage number from 0-100 as the fan speed level.
    """

    def __init__(self, index, valuePaths):

        if 'speed' not in valuePaths and 'pwm' not in valuePaths:
            raise AssertionError("Invalid Paths")

        self.index = index
        self.level = False
        self.sysfs = SysFS(valuePaths)
        self.detect()


    def detect(self):
        self.speed = self.round(int(self.sysfs.get('speed', [self.index])) / 2.55)
        if self.level == False:
            self.level = self.speed

        self.pwm = self.round(self.sysfs.get('pwm', [self.index]))
        return self


    def round(self, number):
        return int(math.ceil(float(number)))


    def setSpeed(self, speed):
        if self.isNotAtLevel(level):
            self.level = speed
            speed = self.round(speed)
            self.sysfs.set('speed', self.round(speed * 2.55), [self.index])
            self.speed = speed


    def isNotAtLevel(self, level):
        return self.level != level


    def enablePWM(self):
        self.sysfs.set('pwm', 0, [self.index])
        self.pwm = 0


    def disablePWM(self):
        self.sysfs.set('pwm', 1, [self.index])
        self.pwm = 1


    def reset(self):
        self.enablePWM()