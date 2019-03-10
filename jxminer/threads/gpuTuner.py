import time
from threads import Thread
from entities import *
from modules import *

class gpuTuner(Thread):

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


    def getSection(self, key, c, unit):
        x = False
        for section in [ '%s|%s|%s' % (key, unit.index, self.coin), '%s|%s' % (key, unit.index), '%s|%s' % (key, self.coin), key ] :
            if c[section] :
                x = section
                break

        unit.configSection = x

        return c[x] if x else x


    def getLevel(self, m, t, u, c, l):
        if m == 'static':
            x = t.max

        elif m == 'time':
            h = time.strftime('%H')
            x = t.min if (h < c.settings.minhour or h >= c.settings.maxhour) else t.max

        else:
            x = UtilCalculateStep(t.min, t.max, l, u.temperature, t.target, t.up, t.down)

        return x
        

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
        tuner = self.getSection(key, c, unit)
        level = getattr(unit, '%sLevel' % key)

        if tuner and level and unit.supportLevels and tuner.enable and (int(unit.temperature) != int(tuner.target) or mode == 'static'):
            unit.detect()
            newLevel = self.getLevel(mode, tuner, unit, c, level)
            if unit.isNotAtLevel(key, unit.round(newLevel)):
                unit.tune(**{ key : newLevel})
                Logger.printLog('Tuning GPU %s:%s %s level to %s%%' % (unit.index, unit.configSection, mode, newLevel), 'success')
