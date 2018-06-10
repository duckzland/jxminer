#!/usr/bin/env bash

echo "[-] Removing dependencies installed from repository"
apt remove python-psutil python-pexpect python-setuptools python-websocket python-scapy python-systemd

echo "[-] Removing dependencies installed from pip"
pip uninstall psutil pexpect setuptools websocket websocket-client scapy systemd addict slackclient requests urllib3 chardet idna certifi backports.ssl_match_hostname

