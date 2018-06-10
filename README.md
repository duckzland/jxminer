

Recommended installation steps:
    1. Update pip
        easy_install --upgrade pip
        
    2. Install the dependencies from apt
        apt install libsystemd-dev
        apt install python-nfqueue
        
    3. Install python deps:
        pip install psutil pexpect setuptools websocket websocket-client scapy systemd addict slackclient requests chardet idna certifi backports.ssl_match_hostname
        
    4. Install JXMiner deb :
        dpkg -i python-jxminer_{VERSION}_all.deb

        
