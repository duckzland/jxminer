
from thread import Thread
from entities.job import *
from modules.utility import calculateStep, printLog

class gpuFansThread(Thread):

    def __init__(self, start, Config, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config
        self.GPUUnits = GPUUnits
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config['fans'].getint('gpu', 'tick'), self.update)


    def update(self, runner):
        c = self.config['fans']
        coin = self.config['machine'].get('gpu_miner', 'coin')

        for unit in self.GPUUnits:
            unit.detect()

            type = 'gpu'
            for section in [ 'gpu|%s|%s' % (unit.index, coin), 'gpu|%s' % (unit.index), 'gpu|%s' % (coin) ] :
                if c.has_section(section) :
                    type = section
                    break

            if int(unit.temperature) != int(c.get(type, 'target')):
                newSpeed = calculateStep(c.get(type, 'min'), c.get(type, 'max'), unit.fanSpeed, c.get(type, 'target'), unit.temperature, c.get(type, 'up'), c.get(type, 'down'))
                if int(newSpeed) != int(unit.fanSpeed):
                    try:
                        unit.tune(fan = newSpeed)
                        status = 'success'
                    except:
                        status = 'error'
                    finally:
                        printLog('Set GPU:%s fan speed to %s%% [%sC]' % (unit.index, newSpeed, unit.temperature), status)