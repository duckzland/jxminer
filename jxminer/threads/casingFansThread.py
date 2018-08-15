
from thread import Thread
from entities.job import *
from entities.config import *
from modules.utility import getHighestTemps, getAverageTemps, calculateStep, printLog
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


    def update(self, runner):
        temperature = None
        c = self.config.data.config.fans

        if c.casing.strategy == 'highest':
            temperature = getHighestTemps(self.GPUUnits)

        elif c.casing.strategy == 'average':
            temperature = getAverageTemps(self.GPUUnits)

        for unit in self.FanUnits:
            unit.detect()
            type = False
            newSpeed = False

            for section in [ 'casing|%s|%s' % (unit.index, self.coin), 'casing|%s' % (unit.index), 'casing|%s' % (self.coin), 'casing' ] :
                if c[section] :
                    type = section
                    break

            fan = c[type]

            if type and int(unit.pwm) != 1:
                unit.disablePWM()

            if type and int(temperature) != int(fan.target):

                # try curve if available
                if fan.curve_enable:
                    curve = fan.curve
                    if curve:
                        cp = Curve(curve)
                        newSpeed = cp.evaluate(int(temperature))

                # fallback to steps
                if not newSpeed:
                    newSpeed = calculateStep(fan.min, fan.max, unit.speed, fan.target, temperature, fan.up, fan.down)


            if newSpeed and int(newSpeed) != int(unit.level):
                try:
                    status = 'success'
                    unit.setSpeed(newSpeed)
                except:
                    status = 'error'
                finally:
                    printLog('Set PWM:%s fan speed to %s%% [%sC]' % (unit.index.replace('pwm', ''), newSpeed, temperature), status)