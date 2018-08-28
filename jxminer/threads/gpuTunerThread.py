import time
from thread import Thread
from entities.job import *
from entities.config import *
from entities.logger import *

from modules.utility import calculateStep

class gpuTunerThread(Thread):

    """
        This is a class for managing threads for tuning gpu
    """


    def __init__(self, start, units):

        self.active = False
        self.job = False
        self.config = Config()
        self.units = units
        self.mode = self.config.data.config.tuner.settings.mode
        self.coin = self.config.data.config.machine.gpu_miner.coin
        self.settings = self.config.data.config.tuner.settings

        self.tick = 20
        if (self.mode == 'dynamic' and 'tick' in self.settings):
            self.tick = self.settings.tick

        if (self.mode == 'static'):
            self.tick = 999999

        if (self.mode == 'time'):
            self.tick = 3600

        self.init()
        if start:
            self.start()
            
    def init(self):
        self.job = Job(self.tick, self.update)


    def update(self, runner):
        for unit in self.units:
            self.tune(unit, 'core', self.mode)
            self.tune(unit, 'memory', self.mode)
            self.tune(unit, 'power', self.mode)

        # only tune once in static mode
        if self.mode == 'static':
            self.destroy()


    def tune(self, unit, key, mode):
        c = self.config.data.config.tuner
        levelKey = key + 'Level'
        type = False

        for section in [ '%s|%s|%s' % (key, unit.index, self.coin), '%s|%s' % (key, unit.index), '%s|%s' % (key, self.coin), key ] :
            if c[section] and c[section]:
                type = section
                break

        tuner = c[type]

        if type and unit.supportLevels and getattr(unit, levelKey) and tuner.enable:
            unit.detect()
            level = getattr(unit, levelKey)
            modeText = mode
            newLevel = False

            if mode == 'static':
                newLevel = tuner.max

            elif int(unit.temperature) != int(tuner.target):
                if mode == 'dynamic':
                    newLevel = calculateStep(tuner.min, tuner.max, getattr(unit, levelKey), unit.temperature, tuner.target, tuner.up, tuner.down)

                if mode == 'time':
                    hour = time.strftime('%H')
                    newLevel = tuner.min if (hour < c.settings.minHour or hour >= c.settings.maxHour) else tuner.max
                    modeText = 'time based'

            if newLevel and int(newLevel) != int(level):
                try:
                    unit.tune(**{ key : newLevel})
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    Logger.printLog('Tuning GPU %s:%s %s level to %s%%' % (unit.index, type, modeText, newLevel), status)