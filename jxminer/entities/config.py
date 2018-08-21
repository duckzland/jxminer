import os, ConfigParser, json
from addict import Dict
from modules.utility import printLog
from shutil import rmtree

class Config:

    """
        Class for managing apps configuration
    """

    data = Dict()
    newData = Dict()
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
    ]

    maps = Dict({
        'config': [
            'coins.ini',
            'fans.ini',
            'machine.ini',
            'miner.ini',
            'notification.ini',
            'sensors.ini',
            'slack.ini',
            'systemd.ini',
            'tuner.ini',
            'watchdog.ini',
        ],
        'miners': [
            'amdxmrig.ini',
            'ccminer.ini',
            'claymore.ini',
            'cpuminer.ini',
            'cpuxmrig.ini',
            'ethminer.ini',
            'ewbf.ini',
            'nheqminer.ini',
            'nvidiaxmrig.ini',
            'sgminer.ini',
        ],
        'pools': [
            '2miners.ini',
            'blockcruncher.ini',
            'coinmine.ini',
            'cryptopool.ini',
            'dwarfpool.ini',
            'flypool.ini',
            'intensecoin.ini',
            'minepool.ini',
            'nanopool.ini',
            'pickaxe.ini',
            'ravenminer.ini',
            'turtlepool.ini'
        ]

    })


    def __init__(self, path = None):
        if path != None:
            Config.path = path


    def scan(self, all = False):
        distDir = os.path.join('/etc', 'jxminer')
        userDir = os.path.join('/home', 'jxminer', '.jxminer')
        extraFiles = Dict()

        for type, files in Config.maps.iteritems():
            for file in files:
                required = all
                if not all and type + '/' + file in Config.required:
                    required = True

                if type == 'pools' and os.path.isdir(userDir + '/pools'):
                    required = False

                self.load(type, file, required)

        # Load extra files that might be defined by user
        if all:
            for path in [ distDir, userDir ]:
                for type, files in Config.maps.iteritems():
                    dir = path + '/' + type
                    if os.path.isdir(dir):
                        for file in os.listdir(dir):
                            if file.lower().endswith('.ini') and file not in files:
                                extraFiles[file] = Dict({
                                    'type': type,
                                    'path': path,
                                    'file': file,
                                })

            for key, file in extraFiles.iteritems():
                self.load(file.type, file.file);


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
        for dir, content in Config.newData.iteritems():
            if dir == 'dynamic':
                continue

            if dir == 'pools':
                basepath = os.path.join('/home', 'jxminer', '.jxminer', 'pools')
                if os.path.isdir(basepath):
                    rmtree(basepath)
                    os.makedirs(basepath)

            for name, file in content.iteritems():

                filename = name.lower() + '.ini'
                savePath = os.path.join('/home', 'jxminer', '.jxminer', dir, filename)
                conf = ConfigParser.ConfigParser(allow_no_value=True)
                
                for section, entries in file.iteritems():
                    conf.add_section(section)
                    if entries:
                        for option, value in entries.iteritems():

                            if (value == True):
                                value = 'true'

                            if (value == False):
                                value = 'false'

                            conf.set(section, option, value)

                if not os.path.isdir(os.path.dirname(savePath)):
                    os.makedirs(os.path.dirname(savePath))

                with open(savePath, 'w') as f:
                    conf.write(f)


    def insert(self, data, isJson = False):
        Config.newData = Dict()
        payload = data
        if data and isJson:
            try:
                while True:
                    # Crude fix for broken json due to bad javascript struct first 4 bytes
                    if payload[0] is not "{":
                        payload = payload[1:]
                    else:
                        break;

                payload = json.loads(payload)

            except Exception as e:
                printLog('Failed to insert configuration: %s' % (e), 'error')
                return

        if isinstance(payload, dict):
            for dir, content in payload.iteritems():

                Config.newData[dir] = Dict()

                for name, file in content.iteritems():
                    if name == '':
                        continue

                    if isinstance(file, dict):
                        for section, entries in file.iteritems():
                            if entries and isinstance(entries, dict):
                                if 'config' in dir:
                                    if name == 'tuner' and section != 'settings' and not self.validateTuner(entries):
                                        continue

                                    if name == 'fans'  and section != 'settings' and not self.validateFans(entries):
                                        continue

                                for option, value in entries.iteritems():
                                    if (value == 'true'):
                                        value = True

                                    if (value == 'false'):
                                        value = False

                                    Config.newData[dir][name][section][option] = value


    def validateTuner(self, entries):
        return entries.get('target', '') != '' and entries.get('min', '') != '' and entries.get('max', '') != '' and entries.get('up', '') != '' and entries.get('down', '') != ''


    def validateFans(self, entries):
        if entries.get('curve_enable', False):
            return entries.get('curve', '') != ''
        else:
            return entries.get('target', '') != '' and entries.get('min', '') != '' and entries.get('max', '') != '' and entries.get('up', '') != '' and entries.get('down', '') != ''


    def extract(self):
        return Config.data


    def reset(self):
        Config.data = Dict()
        Config.newData = Dict()
