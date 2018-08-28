from thread import Thread
from entities.job import *
from entities.config import *
from entities.logger import *
from modules.utility import calculateStep
from modules.curve import Curve

class gpuFansThread(Thread):

    """
        This is a class for managing threads for tuning gpu fans
    """


    def __init__(self, start, units):
        self.active = False
        self.job = False
        self.config = Config()
        self.units = units
        self.coin = self.config.data.config.machine.gpu_miner.coin

        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config.data.config.fans.gpu.tick, self.update)


    def update(self, runner):
        c = self.config.data.config.fans

        for unit in self.units:
            unit.detect()
            type = False
            newSpeed = False

            for section in [ 'gpu|%s|%s' % (unit.index, self.coin), 'gpu|%s' % (unit.index), 'gpu|%s' % (self.coin), 'gpu' ] :
                if c[section] :
                    type = section
                    break

            fan = c[type]

            if type and fan.enable:
                if int(unit.temperature) != int(fan.target):

                    # try curve if available
                    if fan.curve_enable:
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
                    Logger.printLog('Set GPU:%s fan speed to %s%% [%sC]' % (unit.index, newSpeed, unit.temperature), status)