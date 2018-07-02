#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = "jxminer",
    version = "0.3.16",
    author = "Jason Xie",
    author_email = "jason.xie@victheme.com",
    description = "Python script for managing mining server",
    packages=['jxminer', 'jxminer.entities', 'jxminer.miners', 'jxminer.miners', 'jxminer.modules', 'jxminer.threads'],
    package_dir={'jxminer' : 'jxminer'},
    include_package_data=True,
    package_data={'': ['data/config/*.ini', 'data/miners/*.ini', 'data/pools/*.ini']},
    data_files=[
        ('/etc/jxminer/config', [
            'jxminer/data/config/coins.ini',
            'jxminer/data/config/fans.ini',
            'jxminer/data/config/machine.ini',
            'jxminer/data/config/miner.ini',
            'jxminer/data/config/sensors.ini',
            'jxminer/data/config/tuner.ini',
            'jxminer/data/config/systemd.ini',
            'jxminer/data/config/slack.ini',
            'jxminer/data/config/notification.ini',
        ]),
        ('/etc/jxminer/miners', [
            'jxminer/data/miners/ccminer.ini',
            'jxminer/data/miners/claymore.ini',
            'jxminer/data/miners/cpuminer.ini',
            'jxminer/data/miners/cpuxmrig.ini',
            'jxminer/data/miners/ethminer.ini',
            'jxminer/data/miners/ewbf.ini',
            'jxminer/data/miners/nheqminer.ini',
            'jxminer/data/miners/sgminer.ini',
        ]),
        ('/etc/jxminer/pools', [
            'jxminer/data/pools/2miners.ini',
            'jxminer/data/pools/cryptopool.ini',
            'jxminer/data/pools/flypool.ini',
            'jxminer/data/pools/krawww-miner.ini',
            'jxminer/data/pools/nanopool.ini',
            'jxminer/data/pools/turtlepool.ini',
            'jxminer/data/pools/coinmine.ini',
            'jxminer/data/pools/dwarfpool.ini',
            'jxminer/data/pools/intensecoin.ini',
            'jxminer/data/pools/minepool.ini',
            'jxminer/data/pools/ravenminer.ini',
        ]),

    ],
    install_requires=[
        'psutil',
        'pexpect',
        'setuptools',
        'websocket',
        'scapy',
        'systemd-python',
        #'nfqueue',
        'addict',
        'slackclient',
    ],
    entry_points = {
        'console_scripts' : ['jxminer = jxminer.jxminer:main']
    },
)
