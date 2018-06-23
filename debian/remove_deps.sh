#!/usr/bin/env bash

echo "[-] Removing dependencies installed from repository"
apt remove python-psutil python-pexpect python-setuptools python-websocket python-scapy python-systemd

echo "[-] Removing dependencies installed from pip"
pip uninstall psutil
pip uninstall pexpect
pip uninstall setuptools
pip uninstall websocket
pip uninstall websocket-client
pip uninstall scapy
pip uninstall systemd
pip uninstall addict
pip uninstall slackclient
pip uninstall requests
pip uninstall urllib3
pip uninstall chardet
pip uninstall idna
pip uninstall certifi
pip uninstall backports.ssl_match_hostname
pip uninstall urllib3

