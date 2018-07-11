
from thread import Thread
from entities.job import *
from modules.utility import getHighestTemps, getAverageTemps, calculateStep, printLog
from modules.curve import Curve

class casingFansThread(Thread):

    """
        This is a class for managing threads for tuning casing fans
    """


    def __init__(self, start, Config, FanUnits, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config
        self.GPUUnits = GPUUnits
        self.FanUnits = FanUnits
        self.coin = self.config['machine'].get('gpu_miner', 'coin')
        self.init()
        if start:
            self.start()

    def init(self):
        self.job = Job(self.config['fans'].getint('casing', 'tick'), self.update)


    def update(self, runner):
        temperature = None
        c = self.config['fans']

        if c.get('casing', 'strategy') == 'highest':
            temperature = getHighestTemps(self.GPUUnits)

        elif c.get('casing', 'strategy') == 'average':
            temperature = getAverageTemps(self.GPUUnits)

        for unit in self.FanUnits:
            unit.detect()
            type = False
            newSpeed = False

            for section in [ 'casing|%s|%s' % (unit.index, self.coin), 'casing|%s' % (unit.index), 'casing|%s' % (self.coin), 'casing' ] :
                if c.has_section(section) :
                    type = section
                    break

            if type and int(unit.pwm) != 1:
                unit.disablePWM()

            if type and int(temperature) != int(c.get(type, 'target')):

                # try curve if available
                curve = c.get(type, 'curve', False)
                if curve:
                    cp = Curve(curve)
                    newSpeed = cp.evaluate(int(temperature))

                # fallback to steps
                if not newSpeed:
                    newSpeed = calculateStep(c.get(type, 'min'), c.get(type, 'max'), unit.speed, c.get(type, 'target'), temperature, c.get(type, 'up'), c.get(type, 'down'))


            if newSpeed and int(newSpeed) != int(unit.level):
                try:
                    status = 'success'
                    unit.setSpeed(newSpeed)
                except:
                    status = 'error'
                finally:
                    printLog('Set PWM:%s fan speed to %s%% [%sC]' % (unit.index.replace('pwm', ''), newSpeed, temperature), status)