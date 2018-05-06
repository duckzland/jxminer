import os
from distutils.core import setup

setup(
    name = "JXMiner",
    version = "0.1-alpha",
    author = "Jason Xie",
    author_email = "jason.xie@victheme.com",
    description = "Python script for managing mining server",
    packages=['jxminer', 'jxminer.threads', 'jxminer.modules', 'jxminer.miners', 'jxminer.entities'],
    package_dir={'jxminer': 'src'},
    package_data={'jxminer': ['data/config/*.ini', 'data/miners/*.ini', 'data/pools/*.ini']},
    data_files=[
        ('/etc/jxminer/config', [
            'src/data/config/coins.ini',
            'src/data/config/fans.ini',
            'src/data/config/machine.ini',
            'src/data/config/miner.ini',
            'src/data/config/sensors.ini',
            'src/data/config/tuner.ini',
        ]),
        ('/etc/jxminer/miners', [
            'src/data/miners/ccminer.ini',
            'src/data/miners/claymore.ini',
            'src/data/miners/cpuminer.ini',
            'src/data/miners/ethminer.ini',
            'src/data/miners/ewbf.ini',
            'src/data/miners/nheqminer.ini',
            'src/data/miners/sgminer.ini',
            'src/data/miners/xmrig.ini',
        ]),
        ('/etc/jxminer/pools', [
            'src/data/pools/2miners.ini',
            'src/data/pools/cryptopool.ini',
            'src/data/pools/flypool.ini',
            'src/data/pools/krawww-miner.ini',
            'src/data/pools/nanopool.ini',
            'src/data/pools/turtlepool.ini',
            'src/data/pools/coinmine.ini',
            'src/data/pools/dwarfpool.ini',
            'src/data/pools/intensecoin.ini',
            'src/data/pools/minepool.ini',
            'src/data/pools/ravenminer.ini',
        ]),

    ],
    entry_points = {
        'console_scripts' : ['jxminer = jxminer.jxminer:main']
    },
)