import os, ConfigParser, json
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


    def scan(self, all = False):
        for type in os.listdir(Config.default):
            for file in os.listdir(os.path.join(Config.default, type)):
                if file.lower().endswith('.ini'):
                    required = all
                    if not all:
                        required = type + '/' + file in Config.required
                    self.load(type, file, required)


    def load(self, type, file, required = False):
        conf = ConfigParser.ConfigParser(allow_no_value=True)
        name = file.lower().replace('.ini', '')

        localPath = os.path.join('/etc', 'jxminer', type, file)
        userPath = os.path.join('/home', 'jxminer', '.jxminer', type, file)

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

                        Config.data[type][name][section.lower()][key] = val

                status = 'success'

            except:
                status = 'error'

            finally:
                printLog('Loading %s configuration from %s' % (name, path), status)



    def save(self):
        ORIG_DEFAULTSECT = ConfigParser.DEFAULTSECT
        for dir, content in Config.data.iteritems():
            if dir == 'dynamic':
                continue

            for name, file in content.iteritems():

                filename = name.lower() + '.ini'
                savePath = os.path.join('/home', 'jxminer', '.jxminer', dir, filename)
                conf = ConfigParser.ConfigParser(allow_no_value=True)
                
                for section, entries in file.iteritems():

                    if section != 'default':
                        ConfigParser.DEFAULTSECT = ORIG_DEFAULTSECT
                        conf.add_section(section)
                    else:
                        ConfigParser.DEFAULTSECT = 'default'

                    if entries:
                        for option, value in entries.iteritems():

                            if (value == True):
                                value = 'true'

                            if (value == False):
                                value = 'false'

                            if section != 'default':
                                conf.set(section, option, value)
                            else:
                                conf.set(ConfigParser.DEFAULTSECT, option, value)

                if not os.path.isdir(os.path.dirname(savePath)):
                    os.makedirs(os.path.dirname(savePath))

                with open(savePath, 'w') as f:
                    conf.write(f)


    def insert(self, data, isJson = False):
        payload = data
        if data and isJson:
            try:
                payload = json.loads(payload)
            except Exception as e:
                printLog(str(e), 'error')

        for dir, content in payload.iteritems():
            for name, file in content.iteritems():
                for section, entries in file.iteritems():
                    if entries:
                        for option, value in entries.iteritems():
                            if (value == 'true'):
                                value = True

                            if (value == 'false'):
                                value = False

                            Config.data[dir][name][section][option] = value



    def extract(self):
        return Config.data
