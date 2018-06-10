#!/usr/bin/env bash

echo "[+] Updating pip"
easy_install --upgrade pip

echo "[+] Installing dependencies from repository"
apt install libsystemd-dev python-nfqueue

echo "[+] Manually reinstall python setup tools"
wget https://bootstrap.pypa.io/ez_setup.py -O - | python

echo "[+] Installing dependencies from pip"
pip install requests urllib3 setuptools psutil pexpect websocket websocket-client scapy systemd addict slackclient chardet idna certifi backports.ssl_match_hostname
