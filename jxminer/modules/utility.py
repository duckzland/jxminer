import os, fnmatch, re

from datetime import datetime
from slackclient import SlackClient
from entities import *

def UtilSendSlack(message):

    c = False
    try:
        c = Config.data.config.slack.settings

    except Exception as e:
        Logger.printLog('Failed to retrieve slack configuration' , 'error')
        Logger.printLog(str(e), 'error')

    if message and c and c.enable:
        try:
            s = SlackClient(c.token)
            output = "[{0}] {1}".format(datetime.now().strftime('%m-%d %H:%M'), message)
            s.api_call("chat.postMessage", channel=c.channel, text=output)

        except Exception as e:
            Logger.printLog('Failed to send message via slack' , 'error')
            Logger.printLog(str(e), 'error')



def UtilGetHighestTemps(GPUUnits):
    temps = []
    for unit in GPUUnits:
        unit.detect()
        temps.append(unit.temperature)

    return int(round(max(temps), 2))



def UtilGetAverageTemps(GPUUnits):
    temps = []
    for unit in GPUUnits:
        unit.detect()
        temps.append(unit.temperature)

    return int(round(float(sum(temps)) / max(len(temps), 1), 2))



def UtilCalculateStep(minStep, maxStep, currentStep, targetTemp, currentTemp, stepUp=None, stepDown=None):
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


def UtilExplode(option, sep=',', chars=None):
    return [ chunk.strip(chars) for chunk in option.split(sep) ]


def UtilWhich(name):
    found = None
    for path in os.getenv("PATH").split(os.path.pathsep):
        full_path = os.path.join(path,name)
        if os.path.exists(full_path):
            found = full_path
            break
    return found


def UtilFindFile(directory, search):
    files = UtilRecursiveGlob(directory, search)
    file = False
    if files and len(files):
        file = files[0]

    return file


def UtilRecursiveGlob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        try:
            goodfiles = fnmatch.filter(files, pattern)
            results.extend(os.path.join(base, f) for f in goodfiles)
        except:
            pass
    return results

def UtilGetOption(name, default, extra):
    if extra and name in extra:
        return extra[name]
    elif name in default:
        return default[name]
    else:
        return None


def UtilStripAnsi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)
