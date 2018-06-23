#!/usr/bin/env bash

echo "[+] Updating pip"
easy_install --upgrade pip

echo "[+] Installing dependencies from repository"
apt install libsystemd-dev python-nfqueue

#echo "[+] Manually reinstall python setup tools"
#wget https://bootstrap.pypa.io/ez_setup.py -O - | python

echo "[+] Manually installing python requests and urllib3"
pip install requests urllib3

echo "[+] Installing python setuptools from ubuntu repository"
apt install python-setuptools

echo "[+] Installing PSUtil, PExpect and Addict dependencies from pip"
pip install psutil
pip install pexpect
pip install addict

echo "[+] Installing python systemd and its dependencies from pip"
apt install libsystemd-dev pkg-config
pip install systemd-python

echo "[+] Installing scapy"
pip install scapy

echo "[+] Installing Websocket, websocket-client and its dependencies from pip"
pip install websocket

echo "[+] Installing slackclient and its dependencies from pip"
pip install --upgrade 'websocket-client >=0.35, <1.0a0'
pip install --upgrade 'requests >=2.11, <3.0a0'
pip install --upgrade 'six >=1.10, <2.0a0'
pip install slackclient
