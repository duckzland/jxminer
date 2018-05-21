import time
from thread import Thread
from entities.job import *
from modules.utility import calculateStep, printLog

class gpuTunerThread(Thread):

    def __init__(self, start, Config, GPUUnits):
        self.active = False
        self.job = False
        self.config = Config
        self.GPUUnits = GPUUnits
        self.init()
        if start:
            self.start()
            
    def init(self):
        self.job = Job(self.config['tuner'].getint('settings', 'tick'), self.update)


    def update(self, runner):
        c = self.config['tuner']
        mode = c.get('settings', 'mode')
        for unit in self.GPUUnits:
            self.tune(unit, 'core', mode)
            self.tune(unit, 'memory', mode)
            self.tune(unit, 'power', mode)


    def tune(self, unit, type, mode):
        c = self.config['tuner']
        levelKey = type + 'Level'
        if unit.supportLevels and getattr(unit, levelKey) and c.getboolean(type, 'enable'):
            level = getattr(unit, levelKey)

            if mode == 'static':
                unit.detect()
                newLevel = c.get(type,  'max')
                if int(newLevel) != int(level):
                    try:
                        unit.tune(**{ type : c.get(type,  'max')})
                        status = 'success'
                    except:
                        status = 'error'
                    finally:
                        printLog('Tuning GPU %s:%s static level to %s%%' % (unit.index, type, newLevel), status)

            elif int(unit.temperature) != int(c.get(type,  'target')):
                if mode == 'dynamic':
                    unit.detect()
                    newLevel = calculateStep(c.get(type, 'min'), c.get(type, 'max'), getattr(unit, levelKey), unit.temperature, c.get(type, 'target'), c.get(type, 'up'), c.get(type, 'down'))
                    if int(newLevel) != int(level):
                        try:
                            unit.tune(**{ type : newLevel})
                            status = 'success'
                        except:
                            status = 'error'
                        finally:
                            printLog('Tuning GPU %s:%s dynamic level to %s%% [%sC]' % (unit.index, type, newLevel, unit.temperature), status)


                if mode == 'time':
                    hour = time.strftime('%H')
                    newLevel = c.get(type,  'min') if (hour < c.get('settings', 'minHour') or hour >= c.get('settings', 'maxHour')) else c.get(type,  'max')
                    if int(newLevel) != int(level):
                        try:
                            unit.tune(**{ type : newLevel})
                            status = 'success'
                        except:
                            status = 'error'
                        finally:
                            printLog('Tuning GPU %s:%s time based level to %s%% [%sC]' % (unit.index, type, newLevel, unit.temperature), status)