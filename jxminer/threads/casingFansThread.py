
from thread import Thread
from entities.job import *
from entities.config import *
from entities.logger import *
from modules.utility import getHighestTemps, getAverageTemps, calculateStep
from modules.curve import Curve

class casingFansThread(Thread):

    """
        This is a class for managing threads for tuning casing fans
    """


    def __init__(self, start, FanUnits, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config()
        self.GPUUnits = GPUUnits
        self.FanUnits = FanUnits
        self.coin = self.config.data.config.machine.gpu_miner.coin
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config.data.config.fans.casing.tick, self.update)

        for unit in self.FanUnits:
            unit.disablePWM()



    def getFan(self, c, unit):
        x = False
        for section in [ 'casing|%s|%s' % (unit.index, self.coin), 'casing|%s' % (unit.index), 'casing|%s' % (self.coin), 'casing' ] :
            if c[section] :
                x = section
                break

        return c[x] if x else x


    def getTemperature(self, s):
        t = None
        if s == 'highest':
            t = getHighestTemps(self.GPUUnits)

        elif s == 'average':
            t = getAverageTemps(self.GPUUnits)

        return t


    def getSpeed(self, u, f, t):
        if f.curve_enable and f.curve:
            cp = Curve(f.curve)
            s = cp.evaluate(int(t))
        else:
            s = calculateStep(f.min, f.max, u.speed, f.target, t, f.up, f.down)

        return s


    def update(self, runner):
        c = self.config.data.config.fans
        temp = self.getTemperature(c.casing.strategy)

        for unit in self.FanUnits:
            unit.detect()
            fan = self.getFan(c, unit)

            if fan and int(temp) != int(fan.target):
                newSpeed = self.getSpeed(unit, fan, temp)
                if unit.isNotAtLevel(unit.round(newSpeed)):
                    unit.setSpeed(newSpeed)
                    Logger.printLog('Set PWM:%s fan speed to %s%% [%sC]' % (unit.index.replace('pwm', ''), newSpeed, temp), 'success')