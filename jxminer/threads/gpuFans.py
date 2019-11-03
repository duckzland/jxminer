from threads import Thread
from entities import *
from modules import *

class gpuFans(Thread):

    """
        This is a class for managing threads for tuning gpu fans
    """


    def __init__(self, **kwargs):
        super(gpuFans, self).__init__()
        self.setPauseTime(1)
        self.configure(**kwargs)


    def init(self):
        self.units = self.args.get('cards', False)
        self.coin = self.config.data.config.machine.gpu_miner.coin
        self.setPauseTime(self.config.data.config.fans.gpu.tick)

        if self.args.get('start', False):
            self.start()


    def update(self):
        c = self.config.data.config.fans

        for unit in self.units:
            unit.detect()
            fan = self.getFan(c, unit)

            if fan and fan.enable and int(unit.temperature) != int(fan.target):
                newSpeed = self.getSpeed(unit, fan)
                if unit.isNotAtLevel('fan', unit.round(newSpeed)):
                    unit.tune(fan = newSpeed)
                    Logger.printLog('Set GPU:%s fan speed to %s%% [%sC]' % (unit.index, newSpeed, unit.temperature), 'success')


    def destroy(self):
        self.stop()
        Logger.printLog("Stopping GPU fans manager", 'success')


    def getFan(self, c, unit):
        x = False
        for section in [ 'gpu|%s|%s' % (unit.index, self.coin), 'gpu|%s' % (unit.index), 'gpu|%s' % (self.coin), 'gpu' ] :
            if c[section] :
                x = section
                break

        return c[x] if x else x


    def getSpeed(self, u, f):
        if f.curve_enable and f.curve:
            cp = Curve(f.curve)
            s = cp.evaluate(int(u.temperature))
        else:
            s = UtilCalculateStep(f.min, f.max, u.fanSpeed, f.target, u.temperature, f.up, f.down)

        return s
