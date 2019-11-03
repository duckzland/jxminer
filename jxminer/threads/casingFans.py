from threads import Thread
from entities import *
from modules import *

class casingFans(Thread):

    """
        This is a class for managing threads for tuning casing fans
    """


    def __init__(self, **kwargs):
        super(casingFans, self).__init__()
        self.setPauseTime(1)
        self.configure(**kwargs)


    def init(self):
        self.GPUUnits = self.args.get('cards', False)
        self.FanUnits = self.args.get('fans', False)
        self.coin = self.config.data.config.machine.gpu_miner.coin
        self.setPauseTime(self.config.data.config.fans.casing.tick)

        for unit in self.FanUnits:
            unit.disablePWM()

        if self.args.get('start', False):
            self.start()


    def update(self):
        c = self.config.data.config.fans
        temp = self.getTemperature(c.casing.strategy)

        for unit in self.FanUnits:
            unit.detect()
            fan = self.getFan(c, unit)

            if fan and int(temp) != int(fan.target):
                newSpeed = self.getSpeed(unit, fan, temp)
                if unit.isNotAtLevel(unit.round(newSpeed)):
                    unit.setSpeed(newSpeed)
                    Logger.printLog('Set PWM:%s fan speed to %s%% [%sC]' % (unit.index.replace('pwm', ''), newSpeed, temp), 'success')


    def destroy(self):
        self.stop()
        Logger.printLog("Stopping casing fans manager", 'success')


    def getFan(self, c, unit):
        x = False
        for section in [ 'casing|%s|%s' % (unit.index, self.coin), 'casing|%s' % (unit.index), 'casing|%s' % (self.coin), 'casing' ] :
            if c[section] :
                x = section
                break

        return c[x] if x else x


    def getTemperature(self, s):
        t = None
        if s == 'highest':
            t = UtilGetHighestTemps(self.GPUUnits)

        elif s == 'average':
            t = UtilGetAverageTemps(self.GPUUnits)

        return t


    def getSpeed(self, u, f, t):
        if f.curve_enable and f.curve:
            cp = Curve(f.curve)
            s = cp.evaluate(int(t))
        else:
            s = UtilCalculateStep(f.min, f.max, u.speed, f.target, t, f.up, f.down)

        return s
