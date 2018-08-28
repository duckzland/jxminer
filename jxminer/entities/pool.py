from entities.config import *
from modules.utility import explode
from entities.logger import *

class Pool:

    """
        This is the class for a single Mining Pool instance
    """

    def __init__(self, pool):
        self.name = pool
        self.config = Config()
        self.config.load('pools', pool + '.ini', True)
        self.init()


    def init(self):
        try:
            self.pool = self.config.data.pools[self.name]
            status = 'success'
        except:
            status = 'error'
            raise
        finally:
            Logger.printLog("Loading %s pool configuration" % (self.name), status)

        self.wallet = self.config.data.config.coins
        self.machine = self.config.data.config.machine


    def replaceToken(self, text):
        return (
            text.replace('{protocol}', self.pool[self.coin].protocol)
                .replace('{port}',     self.pool[self.coin].port)
                .replace('{wallet}',   self.wallet[self.coin].wallet)
                .replace('{worker}',   self.machine.settings.worker)
                .replace('{email}',    self.machine.settings.email)
                .replace('{password}', self.pool[self.coin].password)
        )


    def getPort(self, coin):
        self.coin = coin
        return self.pool[self.coin].port


    def getRawAddress(self, coin):
        self.coin = coin
        return self.pool[self.coin].url

    def getRawProtocol(self, coin):
        return self.pool[self.coin].protocol

    def getAddress(self, coin):
        self.coin = coin
        url = self.pool[self.coin].url
        format = self.pool.format.address
        if format:
            address = self.replaceToken(format).replace('{url}', url)
        else:
            address = url
        return address


    def getWallet(self, coin):
        self.coin = coin
        return self.replaceToken(self.pool.format.wallet)


    def getPassword(self, coin):
        self.coin = coin
        return self.replaceToken(self.pool[self.coin].password)