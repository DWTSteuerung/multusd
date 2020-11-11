# multusd
#


Raspberry Pi fail-safe process and hardware handling framework

A daemon process: multusd, which starts, stops and controlls child processes.

The potential failing of a child process can be surely determined after a configurable, given timespan from 200mS on upwards.
If the child process is in disorder, a certain, configurable system state can be established.

The configuration files of the child processes can be maintained by a http/php configuration tool.

The framework has been developed for the raspberry pi, but runs on all other unix alike systems, except of the hardware classes.

see share/MakeItRunAfterClone.txt

Karl Keusgen
2019 - 2020
