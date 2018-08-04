import os, ConfigParser
from addict import Dict
from modules.utility import printLog

class Config:

    """
        Class for managing apps configuration
    """

    data = Dict()
    path = ''
    default = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    required = [
        'config/machine.ini',
        'config/coins.ini',
        'config/fans.ini',
        'config/miner.ini',
        'config/notification.ini',
        'config/sensors.ini',
        'config/slack.ini',
        'config/sensors.ini',
        'config/tuner.ini',
        'config/watchdog.ini',

        ## Load these dynamically
        #'miners/amdxmrig.ini',
        #'miners/ccminer.ini',
        #'miners/claymore.ini',
        #'miners/cpuminer.ini',
        #'miners/cpuxmrig.ini',
        #'miners/ethminer.ini',
        #'miners/ewbf.ini',
        #'miners/nheqminer.ini',
        #'miners/nvidiaxmrig.ini',
        #'miners/sgminer.ini'
    ]



    def __init__(self, path = None):
        if path != None:
            Config.path = path


    def scan(self):
        for type in os.listdir(Config.default):
            for file in os.listdir(os.path.join(Config.default, type)):
                if file.lower().endswith('.ini'):
                    required = type + '/' + file in Config.required
                    self.load(type, file, required)


    def load(self, type, file, required = False):
        conf = ConfigParser.ConfigParser(allow_no_value=True)
        name = file.lower().replace('.ini', '')

        localPath = os.path.join('/etc', 'jxminer', type, file)
        userPath = os.path.join('~/', '.jxminer', type, file)

        path = False
        if os.path.isfile(userPath):
            path = userPath

        if not path and required:
            if os.path.isfile(localPath):
                path = localPath

            else:
                path = os.path.join(Config.default, type, file)

        if path:
            try:
                conf.read(path)
                for section in conf.sections():
                    for key, val in conf.items(section):

                        if (val == 'true'):
                            val = True

                        if (val == 'false'):
                            val = False

                        Config.data[type][name][section][key] = val

                status = 'success'

            except:
                status = 'error'

            finally:
                printLog('Loading %s configuration from %s' % (name, path), status)



    def save(self):
        pass

    def insert(self, payload):
        pass

    def extract(self):
        pass
