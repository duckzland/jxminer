import os

class SysFS:

    """
        This is a class for defining a sysfs operation
    """

    def __init__(self, valuePaths=None):
        if not valuePaths:
           valuePaths = {}

        self.valuePaths = valuePaths

    def set(self, path, value, path_keys=None):

        if not path_keys:
            path_keys = []

        if not self.valuePaths[path]:
            raise AssertionError("Invalid Path")

        filePath = self.valuePaths[path].replace('%s', '{}').format(*path_keys)

        if not os.path.isfile(filePath):
            raise AssertionError('Cannot write to sysfs file. File does not exist')
            return False

        with open(filePath, 'w') as fs:
            try:
                fs.write(str(value) + '\n')
            except OSError:
                print('Unable to write to sysfs file' + filePath)
                return False
        return True


    def get(self, path, path_keys=None):

        if not path_keys:
            path_keys = []

        if not self.valuePaths[path]:
            raise AssertionError("Invalid Path")

        fileValue = ''
        filePath = self.valuePaths[path].replace('%s', '{}').format(*path_keys)

        if not os.path.isfile(filePath):
            raise AssertionError("File not found")

        with open(filePath, 'r') as fileContents:
            fileValue = fileContents.read().rstrip('\n')

        if fileValue == '':
            raise AssertionError("Empty SysFS Value")

        return fileValue

