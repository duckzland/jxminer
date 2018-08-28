
from datetime import datetime

class Logger():

    """
        Class for storing logger
    """

    buffers = []
    mode = 'normal'


    def __init__(self, mode):
        Logger.mode = mode


    @staticmethod
    def printLog(text, status = 'info', buffer = True, console = True):

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

        if Logger.mode not in ['daemon']:
            output = "[ {0} ][ {1} ] {2}".format(datetime.now().strftime('%m-%d %H:%M'), status, text).strip()

        else:
            output = "[ {0} ] {1}".format(status, text).strip()

        if buffer:
            if len(Logger.buffers) > 10 :
                Logger.buffers.pop(0)
            Logger.buffers.append(output)

        if console:
            print(output)


    @staticmethod
    def getLogBuffers():
        return Logger.buffers