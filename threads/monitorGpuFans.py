import sys
from thread import Thread
sys.path.append('../')
from entities.job import *
from modules.utility import calculateStep, printLog

class MonitorGPUFans(Thread):

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
        for unit in self.GPUUnits:
            unit.detect()
            if int(unit.temperature) != int(c.get('gpu', 'target')):
                newSpeed = calculateStep(c.get('gpu', 'min'), c.get('gpu', 'max'), unit.fanSpeed, c.get('gpu', 'target'), unit.temperature, c.get('gpu', 'up'), c.get('gpu', 'down'))
                if int(newSpeed) != int(unit.fanSpeed):
                    try:
                        unit.tune(fan = newSpeed)
                        status = 'success'
                    except:
                        status = 'error'
                    finally:
                        printLog('Set GPU:%s fan speed to %s%% [%sC]' % (unit.index, newSpeed, unit.temperature), status)