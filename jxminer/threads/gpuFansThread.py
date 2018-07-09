
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
        self.coin = self.config['machine'].get('gpu_miner', 'coin')

        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config['fans'].getint('gpu', 'tick'), self.update)


    def update(self, runner):
        c = self.config['fans']

        for unit in self.GPUUnits:
            unit.detect()
            type = False
            newSpeed = False

            for section in [ 'gpu', 'gpu|%s|%s' % (unit.index, self.coin), 'gpu|%s' % (unit.index), 'gpu|%s' % (self.coin) ] :
                if c.has_section(section) :
                    type = section
                    break

            if type and int(unit.temperature) != int(c.get(type, 'target')):

                # try curve if available
                curve = c.get(type, 'curve', False)
                if curve:
                    cp = Curve(curve)
                    newSpeed = cp.evaluate(int(unit.temperature))

                # fallback to steps
                if not newSpeed:
                    newSpeed = calculateStep(c.get(type, 'min'), c.get(type, 'max'), unit.fanSpeed, c.get(type, 'target'), unit.temperature, c.get(type, 'up'), c.get(type, 'down'))


            if newSpeed and int(newSpeed) != int(unit.fanLevel):
                try:
                    status = 'success'
                    unit.tune(fan = newSpeed)
                except:
                    status = 'error'
                finally:
                    printLog('Set GPU:%s fan speed to %s%% [%sC]' % (unit.index, newSpeed, unit.temperature), status)