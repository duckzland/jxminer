
from thread import Thread
from entities.job import *
from modules.utility import getHighestTemps, getAverageTemps, calculateStep, printLog

class MonitorCasingFans(Thread):

    def __init__(self, start, Config, FanUnits, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config
        self.GPUUnits = GPUUnits
        self.FanUnits = FanUnits
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config['fans'].getint('casing', 'tick'), self.update)


    def update(self, runner):
        temperature = None
        newSpeed = None

        c = self.config['fans']
        if c.get('casing', 'strategy') == 'highest':
            temperature = getHighestTemps(self.GPUUnits)

        elif c.get('casing', 'strategy') == 'average':
            temperature = getAverageTemps(self.GPUUnits)

        for unit in self.FanUnits:
            unit.detect()

            if int(unit.pwm) != 1:
                unit.disablePWM()

            if not newSpeed:
                newSpeed = calculateStep(c.get('casing', 'min'), c.get('casing', 'max'), unit.speed, c.get('casing', 'target'), temperature, c.get('casing', 'up'), c.get('casing', 'down'))

            if int(newSpeed) != int(unit.speed):
                try:
                    unit.setSpeed(newSpeed)
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog('Set fan speed %s:%s%% [%s|%sC]' % (unit.index, newSpeed, c.get('casing', 'strategy'), temperature), status)