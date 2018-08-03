
from thread import Thread
from entities.job import *
from modules.utility import calculateStep, printLog
from modules.curve import Curve

class gpuFansThread(Thread):

    """
        This is a class for managing threads for tuning gpu fans
    """


    def __init__(self, start, Config, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config
        self.GPUUnits = GPUUnits
        self.coin = self.config.data.machine.gpu_miner.coin

        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config.data.fans.gpu.tick, self.update)


    def update(self, runner):
        c = self.config.data.fans

        for unit in self.GPUUnits:
            unit.detect()
            type = False
            newSpeed = False

            for section in [ 'gpu|%s|%s' % (unit.index, self.coin), 'gpu|%s' % (unit.index), 'gpu|%s' % (self.coin), 'gpu' ] :
                if c[section] :
                    type = section
                    break

            fan = c[type]

            if type and int(unit.temperature) != int(fan.target):

                # try curve if available
                curve = fan.curve
                if curve:
                    cp = Curve(curve)
                    newSpeed = cp.evaluate(int(unit.temperature))

                # fallback to steps
                if not newSpeed:
                    newSpeed = calculateStep(fan.min, fan.max, unit.fanSpeed, fan.target, unit.temperature, fan.up, fan.down)


            if newSpeed and int(newSpeed) != int(unit.fanLevel):
                try:
                    status = 'success'
                    unit.tune(fan = newSpeed)
                except:
                    status = 'error'
                finally:
                    printLog('Set GPU:%s fan speed to %s%% [%sC]' % (unit.index, newSpeed, unit.temperature), status)