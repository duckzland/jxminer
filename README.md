# JXMiner

Python script for managing crypto miner instance under Linux OS.

![Alt text](docs/jxminer.png?raw=true "JXMiner Screenshot")

## Features
- Casing Fan speed management, speed is calculated from GPU temperature.
- GPU Fan speed management for both AMD and Nvidia GPU
- GPU Core speed level control for both AMD and Nvidia GPU
- GPU Power level control for Nvidia GPU
- GPU Memory level control for both AMD and Nvidia GPU
- Systemd monitoring for rebooting server when GPU crashed
- Notification system for sending json data to designated server
- CPU miner using xmrrig
- GPU miner supported: ccminer, claymore, ethminer, ewbf, sgminer, xmrig-amd, xmrig-nvidia, cast-xmr
- Notification to Slack
- Casing and GPU fan control with curve mode
- Detect hash rate value and reboot the machine (or just reboot the miner) when it is low


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

### Via JXDashboard
You can use [ JXDashboard ](https://github.com/duckzland/jxdashboard) to monitor JXMiner via GUI interface, Working Xserver is required to use GUI on Linux OS

```bash
    jxdashboard
```

## Server Arguments
The server has several command line arguments that can be used to modify the default value:

```bash
    jxminer -m|-h|-v|-s|-p|-c
```

-m <mode> Run the program as daemon, logging will be minimized
-h Prints the help message
-v Prints the server version
-s Specify the host this server should bind to, by default it will bind to 127.0.0.1 which can only be accessed from local loop
-p Specify the port to bind to
-c Path to configuration files directory


## TODO
Patch or pull request for ironing out the todo list is welcomed.

To test and iron out bugs for :
1. Test Dual mining with claymore
2. Test trully dual GPU miner running at once
3. Test SGMiner and Ethminer integration
4. Test running mixed AMD and Nvidia GPU in the same box
5. Test with more GPU variant (1080ti, 1050ti, RXVega etc)
6. Test with different kind of motherboard motherboard

Future improvement :
1. Add more miner such as xmr-stak
2. Add more sgminer variant to match ccminer supported algo



## Help with Donation
if you found this program useful, consider to donate for the development fund.

Send donation to:
Monero : 49qh7jAS1Tt9C7rcmirWPNbg8p6eon24FQ7K5mTFE1i9ScRUSYDVuWw3MDcadcybhD8uBEhvJtymx4NpYNBSP3Tm5RHxhuY



## Authors

* **Jason Xie** - *Initial work* - [VicTheme.com](https://victheme.com)



## License

This project is licensed under the GNU General Public License - see the [LICENSE](LICENSE) file for details
