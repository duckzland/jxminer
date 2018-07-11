import time
from thread import Thread
from entities.job import *
from modules.utility import calculateStep, printLog

class gpuTunerThread(Thread):

    """
        This is a class for managing threads for tuning gpu
    """


    def __init__(self, start, Config, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config
        self.GPUUnits = GPUUnits
        self.mode = self.config['tuner'].get('settings', 'mode')
        self.coin = self.config['machine'].get('gpu_miner', 'coin')
        self.init()

        if start:
            self.start()
            
    def init(self):
        self.job = Job(self.config['tuner'].getint('settings', 'tick'), self.update)


    def update(self, runner):
        for unit in self.GPUUnits:
            self.tune(unit, 'core', self.mode)
            self.tune(unit, 'memory', self.mode)
            self.tune(unit, 'power', self.mode)

        # only tune once in static mode
        if self.mode == 'static':
            self.destroy()


    def tune(self, unit, key, mode):
        c = self.config['tuner']
        levelKey = key + 'Level'
        type = False

        for section in [ '%s|%s|%s' % (key, unit.index, self.coin), '%s|%s' % (key, unit.index), '%s|%s' % (key, self.coin), key ] :
            if c.has_section(section) :
                type = section
                break

        if type and unit.supportLevels and getattr(unit, levelKey) and c.getboolean(type, 'enable'):
            unit.detect()
            level = getattr(unit, levelKey)
            modeText = mode
            newLevel = False

            if mode == 'static':
                newLevel = c.get(type, 'max')

            elif int(unit.temperature) != int(c.get(type, 'target')):
                if mode == 'dynamic':
                    newLevel = calculateStep(c.get(type, 'min'), c.get(type, 'max'), getattr(unit, levelKey), unit.temperature, c.get(type, 'target'), c.get(type, 'up'), c.get(type, 'down'))

                if mode == 'time':
                    hour = time.strftime('%H')
                    newLevel = c.get(type, 'min') if (hour < c.get('settings', 'minHour') or hour >= c.get('settings', 'maxHour')) else c.get(type,  'max')
                    modeText = 'time based'

            if newLevel and int(newLevel) != int(level):
                try:
                    unit.tune(**{ key : newLevel})
                    status = 'success'
                except:
                    status = 'error'
                finally:
                    printLog('Tuning GPU %s:%s %s level to %s%%' % (unit.index, type, modeText, newLevel), status)