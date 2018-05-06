import sys
sys.path.append('../')
from modules.utility import explode, printLog

class Pool:

    """
        This is the class for a single Mining Pool instance
    """

    def __init__(self, pool, Config):
        self.init(pool, Config)


    def init(self, pool, Config):
        self.name = pool
        self.config = Config
        try:
            self.pool = self.config[pool]
            status = 'success'
        except:
            status = 'error'
            raise
        finally:
            printLog("Loading %s pool configuration" % (pool), status)

        self.wallet = self.config['coins']
        self.machine = self.config['machine']


    def replaceToken(self, text):
        return (
            text.replace('{protocol}', self.pool.get(self.coin, 'protocol'))
                .replace('{port}', self.pool.get(self.coin, 'port'))
                .replace('{wallet}', self.wallet.get(self.coin, 'wallet'))
                .replace('{worker}', self.machine.get('settings', 'worker'))
                .replace('{email}', self.machine.get('settings', 'email'))
                .replace('{password}', self.pool.get(self.coin, 'password'))
        )


    def getPort(self, coin):
        self.coin = coin
        return self.pool.get(self.coin, 'port')


    def getRawAddress(self, coin):
        self.coin = coin
        return self.pool.get(self.coin, 'url')


    def getAddress(self, coin):
        self.coin = coin
        url = self.pool.get(self.coin, 'url')
        format = self.pool.get('format', 'address')
        if format:
            address = self.replaceToken(format).replace('{url}', url)
        else:
            address = url

        return address


    def getWallet(self, coin):
        self.coin = coin
        return self.replaceToken(self.pool.get('format', 'wallet'))


    def getPassword(self, coin):
        self.coin = coin
        return self.replaceToken(self.pool.get(self.coin, 'password'))