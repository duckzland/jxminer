# JXMiner

Python script for managing crypto miner instance under Linux OS.

![Alt text](docs/jxminer.png?raw=true "JXMiner Screenshot")

## Features
- Casing Fan speed management, speed is calculated from GPU temperature.
- GPU Fan speed management for both AMD and Nvidia GPU
- GPU Core speed level control for both AMD and Nvidia GPU
- GPU Power level control for Nvidia GPU
- GPU Memory level control for Nvidia GPU
- SystemD monitoring for rebooting server when GPU crashed
- Notification system for sending json data to designated server
- CPU miner using xmr-rig
- GPU miner supported: ccminer, claymore, xmr-rig(cpu only), ethminer, ewbf, sgminer
- Notification to Slack


## Requirement
- Nvidia driver installed
- Nvidia-smi installed
- AMDGPU pro driver with compute mode enabled
- OpenCL and/or CUDA properly installed
- Kernel driver for motherboard fan header control installed
- Systemd installed
- Tuning up the server for proper mining machine (eg. large page files for CPU mining)
- Miner software installed in `/usr/local/bin` folder
- Python installed



## Installation (Ubuntu)
1. Install dependencies via apt:
```ubuntu
    sudo apt install libsystemd-dev
    sudo apt install python-nfqueue
```
        
2. Install python dependencies via requirement.txt:
```bash
    sudo pip install -r requirement.txt  
```
    
3. Install the deb
```bash
    sudo dpkg -i python-jxminer-VERSION.deb
```
    


## Configuration
The configuration files will be placed under `/etc/jxminer folder`, at the minimum you must change
the `/etc/jxminer/config/coins.ini` to enter your own wallet address and the `/etc/jxminer/config/machine.ini`
to set what coin to mine.



## Monitoring

### Via SystemD
By default, the `python-jxminer-VERSION.deb` will install the script as a systemd service, then to monitor the script activity
you can use systemd by invoking:

```bash
    sudo journalctl -u jxminer.service -f
```

### Via JXClient
You can use [ JXClient ](https://github.com/duckzland/jxclient) to monitor and control JXMiner via CLI

Monitoring a miner progress:
```bash
    jxclient -a monitor:gpu:0
```

Monitoring server logs:
```bash
    jxclient -a monitor:server
```


### Via JXMonitor
You can use [ JXMonitor ](https://github.com/duckzland/jxmonitor) to monitor JXMiner via TUI interface

```bash
    jxmonitor 
```

Use a single column only for monitoring multiple server instance
```bash
    jxmonitor -s
```





## Authors

* **Jason Xie** - *Initial work* - [VicTheme.com](https://victheme.com)



## License

This project is licensed under the GNU General Public License - see the [LICENSE.md](LICENSE.md) file for details
