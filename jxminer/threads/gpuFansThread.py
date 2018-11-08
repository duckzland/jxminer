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


    def getFan(self, c, unit):
        x = False
        for section in [ 'gpu|%s|%s' % (unit.index, self.coin), 'gpu|%s' % (unit.index), 'gpu|%s' % (self.coin), 'gpu' ] :
            if c[section] :
                x = section
                break

        return c[x] if x else x
        
        
    def getSpeed(self, u, f):
        if f.curve_enable and f.curve:
            cp = Curve(f.curve)
            s = cp.evaluate(int(u.temperature))
        else:
            s = calculateStep(f.min, f.max, u.fanSpeed, f.target, u.temperature, f.up, f.down)
            
        return s


    def update(self, runner):
        c = self.config.data.config.fans

        for unit in self.units:
            unit.detect()
            fan = self.getFan(c, unit)

            if fan and fan.enable and int(unit.temperature) != int(fan.target):
                newSpeed = self.getSpeed(unit, fan)
                if unit.isNotAtLevel('fan', unit.round(newSpeed)):
                    unit.tune(fan = newSpeed)
                    Logger.printLog('Set GPU:%s fan speed to %s%% [%sC]' % (unit.index, newSpeed, unit.temperature), 'success')