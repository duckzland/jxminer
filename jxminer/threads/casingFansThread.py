
from thread import Thread
from entities.job import *
from modules.utility import getHighestTemps, getAverageTemps, calculateStep, printLog

class casingFansThread(Thread):

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
        coin = self.config['machine'].get('gpu_miner', 'coin')

        if c.get('casing', 'strategy') == 'highest':
            temperature = getHighestTemps(self.GPUUnits)

        elif c.get('casing', 'strategy') == 'average':
            temperature = getAverageTemps(self.GPUUnits)

        for unit in self.FanUnits:
            unit.detect()

            type = 'casing'
            for section in [ 'casing|%s|%s' % (unit.index, coin), 'casing|%s' % (unit.index), 'casing|%s' % (coin) ] :
                if c.has_section(section) :
                    type = section
                    break

            if int(unit.pwm) != 1:
                unit.disablePWM()

            if not newSpeed:
                newSpeed = calculateStep(c.get(type, 'min'), c.get(type, 'max'), unit.speed, c.get(type, 'target'), temperature, c.get(type, 'up'), c.get(type, 'down'))

            if int(newSpeed) != int(unit.speed):
                try:
                    unit.setSpeed(newSpeed)
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog('Set PWM:%s fan speed to %s%% [%sC]' % (unit.index.replace('pwm', ''), newSpeed, temperature), status)