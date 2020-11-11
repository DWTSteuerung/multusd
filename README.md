# multusd
#


Raspberry Pi fail-safe process and hardware handling framework

multusd is a daemon process which starts, stops and controlls ist child processes.

The potential failing, crashing or even hanging of a child process can be surely determined after a configurable, given timespan (200ms - seconds ... depending on the processors capabilities and general system load).
If the child process is in disorder, a certain, configurable system state can be established, the child process will be restarted endlessly.

The configuration files of the child processes can be maintained by a http/php configuration tool.

# Why multusd?

- easy setup of new multusd child processes by copying a template process and gainig a lot of standard features right from the start
- every multusd child process is supervised and potentially fail-safe
- every multud child process has a logfile
- every multusd child process has an easy extendable and user maintainable configuration file
- No need to worry about every possible runtime error which may occure.. the process is supervised, it crashes and will be restarted.. It can't be easier, no internal error handling needed


The framework has been developed for the raspberry pi, but runs on all other unix alike systems (except of the hardware classes, which need to be disabled on PC hardware).

# With the multusd there come some usefull processes and a process template

- multusd - the daemon
- multusLAN - LAN configuration via http
- multusOVPNClient - An OpenVPN client
- multusLANWANCheck - Process checking LAN and internet access
- multusOpenVPNCheck - processchecing OpenVPN connectivity
- status-led - a simple process which indicates the status of LAN and VPN by blinking a GPIO
- multusModbus - a modbus server for reading and writing GPIOs
- multusReadDIDO - read in the status of GPIO inputs, or the status of GPIO outputs and transfer this status to other similar multusd devices, so that their outputs go into the same stats than the mother system
- multusdClientTemplate - a template process, which can be take to write new processes and earning the capabilities of this system from the start.. 

see share/MakeItRunAfterClone.txt

see share/SetupOfmultusdChildProcess.txt

see share/multusdHandlingAndConfiguration.txt

Karl Keusgen
2019 - 2020
