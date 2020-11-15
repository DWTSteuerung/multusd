# multusd
Raspberry Pi fail-safe process and hardware handling framework 

multusd is a daemon process which starts, stops and controlls ist child processes. This is the community version of the DWT project which comes without an overall system status daemon. 

The potential failing, crashing or even hanging of a child process can be surely determined after a configurable, given timespan (200ms - seconds ... depending on the child process itself, the processors capabilities and the general system load).
If the child process is in disorder, a certain, configurable system state can be established, the child process will be restarted endlessly.

For inter process communication (IPC) gRPC and protocol-buffers are used.

The configuration files of the child processes can be maintained by a http/php configuration tool.

# Why multusd?
- easy setup of new multusd child processes by copying a template process and gainig a lot of standard features right from the start
- every multusd child process is supervised and potentially fail-safe
- every multud child process has a logfile
- every multusd child process has an easy extendable and user maintainable configuration file
- No more worrying about every possible runtime error which may occure.. the process is supervised, it crashes and will be restarted.. It can't be easier, no internal error handling needed
- Automatic process reload after changing the configuration over the php interface


The framework has been developed for the raspberry pi, but runs on all other unix alike systems (except of the hardware classes, which need to be disabled on PC hardware. See multusd on PC harware manual below).

# With the multusd there come some usefull processes and a process template
- multusd - the daemon
- multusLAN - LAN configuration via http
- multusOVPNClient - An OpenVPN client
- multusLANWANCheck - Process checking LAN and internet access
- multusOpenVPNCheck - processchecing OpenVPN connectivity
- multusStatusLED - a simple process which indicates the status of LAN and VPN by blinking a GPIO (RPi only)
- multusModbus - a modbus server for reading and writing GPIOs (RPi only)
- multusReadDIDO - read in the status of local GPIO inputs, or the status of local GPIO outputs and transfer this status to other similar, network connected multusd devices, so that their outputs go into the same state than the mother system (RPi only)
- multusdClientTemplate - a template process, which can be take to write new processes and earning the capabilities of this system from the start.. 

# Required packages on PC hardware
- python3, python3-pip
- python packages: pip3 install daemonize pymysql grpcio-tools psutil
- Webserver with php runtime environment: apache2 libapache2-mod-php
- openvpn (optional)
- mysql database: mariadb-server (optional) 

# Additional packages on RPi hardware
- pip3 install RPi.GPIO umodbus wiringpi mcp3208
- install MCP4922 which comes with this repository (share/install dir)

For general setup follow the instructions in: share/MakeItRunAfterClone.txt

For instructions, how to integrate a new process into multusd see: share/SetupOfmultusdChildProcess.txt

Some general explanation, of the internal functions of multusd see: share/multusdHandlingAndConfiguration.txt

Karl Keusgen
2019 - 2020

Deutsche Windtechnik Steuerung GmbH & Co. KG, Osterport 2f, D-25872 Ostenfeld

