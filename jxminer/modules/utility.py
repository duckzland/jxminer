import os, fnmatch, re
from datetime import datetime
from slackclient import SlackClient

MainBuffers = []
Config = None
SlackToken = None
SlackChannel = None
SlackEnable = None

def printLog(text, status = 'info', buffer = True, console = True, config = False):
    global MainBuffers
    global Config

    if config:
        Config = config

    mode = False
    if Config and Config.data.dynamic:
        mode = Config.data.dynamic.settings.mode

    if 'error' in status:
        status = '-#' + status + '  #-'

    elif 'info' in status:
        status = '---#' + status + '   #-'

    else:
        status = '--#' + status + '#-'

    status = (
        status
            .upper()
            # Cyan color
            .replace('---#', '\033[36m')

            # Green color
            .replace('--#', '\033[32m')

            # Red color
            .replace('-#', '\033[91m')
            .replace('#-', '\033[0m')
    )

    text = (
        text
            .replace('--#', '\033[32m')
            .replace('-#', '\033[91m')
            .replace('#-', '\033[0m')
    )

    if mode not in ['daemon']:
        output = "[ {0} ][ {1} ] {2}".format(datetime.now().strftime('%m-%d %H:%M'), status, text).strip()

    else:
        output = "[ {0} ] {1}".format(status, text).strip()

    if buffer:
        if len(MainBuffers) > 10 :
            MainBuffers.pop(0)
        MainBuffers.append(output)

    if console:
        print(output)



def sendSlack(message, token = None, channel = None, send = None):
    global SlackChannel
    global SlackToken
    global SlackEnable

    if token:
        SlackToken = token

    if channel:
        SlackChannel = channel

    if send:
        SlackEnable = send

    if message and SlackEnable:
        try:
            s = SlackClient(SlackToken)
            output = "[{0}] {1}".format(datetime.now().strftime('%m-%d %H:%M'), message)
            s.api_call("chat.postMessage", channel=SlackChannel, text=output)
        except Exception as e:
            pass

def getLogBuffers():
    return MainBuffers


def getHighestTemps(GPUUnits):
    temps = []
    for unit in GPUUnits:
        unit.detect()
        temps.append(unit.temperature)

    return int(round(max(temps), 2))



def getAverageTemps(GPUUnits):
    temps = []
    for unit in GPUUnits:
        unit.detect()
        temps.append(unit.temperature)

    return int(round(float(sum(temps)) / max(len(temps), 1), 2))



def calculateStep(minStep, maxStep, currentStep, targetTemp, currentTemp, stepUp=None, stepDown=None):
    if not stepUp:
        stepUp = 7

    if not stepDown:
        stepDown = 1

    currentStep = int(currentStep)

    if int(currentTemp) > int(targetTemp):
        currentStep += int(stepUp)

    elif int(currentTemp) < int(targetTemp):
        currentStep -= int(stepDown)

    return int(max(min(int(maxStep), currentStep), int(minStep)))


def explode(option, sep=',', chars=None):
    return [ chunk.strip(chars) for chunk in option.split(sep) ]


def which(name):
    found = None
    for path in os.getenv("PATH").split(os.path.pathsep):
        full_path = os.path.join(path,name)
        if os.path.exists(full_path):
            found = full_path
            break
    return found


def findFile(directory, search):
    files = recursive_glob(directory, search)
    file = False
    if files and len(files):
        file = files[0]

    return file


def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        try:
            goodfiles = fnmatch.filter(files, pattern)
            results.extend(os.path.join(base, f) for f in goodfiles)
        except:
            pass
    return results

def getOption(name, default, extra):
    if extra and name in extra:
        return extra[name]
    elif name in default:
        return default[name]
    else:
        return None


def stripAnsi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)
