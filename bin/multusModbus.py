#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-
#
# Karl Keusgen
#
# Modbus/TCP Server
# provides Modbus/TCP Access to the multus hardware
#
# 2019-11-16
#

import sys
import time
import os
import signal

from daemonize import Daemonize

sys.path.append('/multus/lib')
import libpidfile
import multusdTools
import multusdConfig
import multusdModuleConfig
import multusHardwareHandler

## do the Periodic Alive Stuff
import multusdControlSocketClient

## this therad is running the Modbus server and handles the requests
import DWTThriftConfig3
import libmultusModbus

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 2020-06-01
# Json config option
if libmultusModbus.UseJsonConfig:
	import libmultusdJson
	import libmultusdJsonModuleConfig

import libmultusdClientBasisStuff

class multusModbusClass(libmultusdClientBasisStuff.multusdClientBasisStuffClass):
	def __init__(self):
		self.ObjmultusdTools = multusdTools.multusdToolsClass()

		## 2020-06-01
		if libmultusModbus.UseJsonConfig:
			# first we get the config of the multusd system
			self.ObjmultusdConfig = libmultusdJson.multusdJsonConfigClass(ObjmultusdTools = self.ObjmultusdTools)
			bSuccess = self.ObjmultusdConfig.ReadConfig()
			if bSuccess:
				ObjmultusdModulesConfig = libmultusdJsonModuleConfig.ClassJsonModuleConfig(self.ObjmultusdConfig, None)
				bSuccess = ObjmultusdModulesConfig.ReadJsonModulesConfig()
			if not bSuccess:
				print ("Something went wrong while reading in the modules.. we leave")
				sys.exit(1)
		else:
			# first we get the config of the multusd system
			self.ObjmultusdConfig = multusdConfig.ConfigDataClass()
			self.ObjmultusdConfig.readConfig()

			## after we got the modules init file.. we have to read it, to get the config files for this process
			ObjmultusdModulesConfig = multusdModuleConfig.ClassModuleConfig(self.ObjmultusdConfig)
			ObjmultusdModulesConfig.ReadModulesConfig()

		self.ProcessIsRunningTwice = True

		#WalkThe list of modules to find our configuration files.. 
		Ident = "multusModbus"
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				if libmultusModbus.UseJsonConfig:
					self.ObjmultusModbusConfig = libmultusModbus.multusModbusConfigClass(None)
					bSuccess = self.ObjmultusModbusConfig.ReadJsonConfig(self.ObjmultusdTools, self.ObjmultusdConfig, Ident)
					if not bSuccess:
						print ("Error getting Json config, we exit")
						sys.exit(2)
				else:
					## get the config data
					self.ObjModbusConfig = libmultusModbus.ModbusConfigClass(Module.ModuleParameter.ModuleConfig)
					self.ObjModbusConfig.ReadConfig()
					self.ObjModbusConfig.ModuleControlPortEnabled = Module.ModuleParameter.ModuleControlPortEnabled 

				# some more parameters
				self.ObjModbusConfig.LPIDFile = Module.ModuleParameter.ModulePIDFile
				self.ObjModbusConfig.ModuleControlPort = Module.ModuleParameter.ModuleControlPort 
				self.ObjModbusConfig.ModuleControlMaxAge = Module.ModuleParameter.ModuleControlMaxAge
				# 2021-02-07
				self.ObjModbusConfig.ModuleControlFileEnabled = Module.ModuleParameter.ModuleControlFileEnabled
				break

		self.LogFile = self.ObjmultusdConfig.LoggingDir +"/" + Module.ModuleParameter.ModuleIdentifier + ".log"
		if self.LogFile:
			## We initialize logging
			self.ObjmultusdTools.InitGlobalLogging(self.LogFile)
		else:
			self.ObjmultusdTools.InitGlobalLogging("/dev/null")

		self.ObjmultusHardware = multusHardwareHandler.multusHardwareHandlerClass(self.ObjModbusConfig, self.ObjmultusdTools)
		# in the Modbus Daemon we need the multusReadDO Extension.. so we initialize it
		self.ObjmultusHardware.InitReadDOStatus()

		# Signal handler initialisieren
		signal.signal(signal.SIGTERM, self.__handler__)
		signal.signal(signal.SIGINT, self.__handler__)

		## Do the PIDFIle
		try:
			print ("We Try to do the PIDFile: " + self.ObjModbusConfig.LPIDFile)
			with(libpidfile.PIDFile(self.ObjModbusConfig.LPIDFile)):
				print ("Writing PID File: " + self.ObjModbusConfig.LPIDFile)
			self.ProcessIsRunningTwice = False
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString + " PIDFile: " + self.ObjModbusConfig.LPIDFile)
			sys.exit(1)

		self.ObjmultusdTools.logger.debug("Started up.. initializing finished")

		# init parent class
		libmultusdClientBasisStuff.multusdClientBasisStuffClass.__init__(self, self.ObjModbusConfig, self.ObjmultusdTools)
		return

	def __del__(self):
		try:
			if not self.ProcessIsRunningTwice:
				os.remove(self.ObjModbusConfig.LPIDFile)
		except:
			ErrorString = self.ObjmultusdTools .FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)

		self.ObjmultusdTools.logger.debug("Instace of Main Class Stopped")

		return

	# Receiving the kill signal, ensure that the heating is off
	def __handler__(self, signum, frame):
		timestr = time.strftime("%Y-%m-%d %H:%M:%S") + " | "

		print (timestr + 'Signal handler called with signal ' + str(signum))
		
		if signum == 15 or signum == 2:
			## We have to stop the Thread
			self.ModbusThread.KeepThreadRunning = False
			self.ObjmultusdTools.logger.debug("Now Shutting down Modbus TCP Server")
			# TODO 
			# if there is an ongoing TCP connection to the server.. we have to force the shutdown somehow
			self.ModbusThread.ObjumodbusServer._shutdown_request = True
			self.ModbusThread.ObjumodbusServer.shutdown()
			self.ObjmultusdTools.logger.debug("Now Closing Modbus TCP Server")
			self.ModbusThread.ObjumodbusServer.server_close()
			self.ModbusThread.join()
			self.ObjmultusdTools.logger.debug("Stopped Modbus Listening Thread")

			count = 0
			while self.ModbusThread.is_alive() and count < 10:
				print ("Waiting thread to terminate")
				time.sleep (1)
				count = count + 1
			
			sys.exit(0)

	############################################################
	###
	### main funtion running the main loop
	###
	def haupt (self, bDeamonized):
		## setup the periodic alive mnessage stuff
		bPeriodicmultusdSocketPingEnable = bDeamonized and self.ModuleControlPortEnabled:
		## setup the periodic control stuff..
		## if this does not succeed .. we do not have to continue
		SleepingTime, self.ModbusThread.KeepThreadRunning = self.SetupPeriodicmessages(bPeriodicmultusdSocketPingEnable)

		nRestart = 0
		MaxRestarts = 10
		## Thread anlegen
		self.ModbusThread = libmultusModbus.multusModbusHandlerThread(self.ObjModbusConfig, self.ObjmultusdTools, self.ObjmultusHardware)
		self.ModbusThread.StartmultusModbusServer()

		self.ModbusThread.KeepThreadRunning = True

		## it the ModBus Process fails too often, we quit... the multusd will restart us again
		while (self.ModbusThread.KeepThreadRunning and nRestart < MaxRestarts):

			## We do the periodic messages and stuff to indicate that we are alive for the multusd
			self.ModbusThread.KeepThreadRunning = self.DoPeriodicMessage(bPeriodicmultusdSocketPingEnable)

			if not self.ModbusThread.is_alive():
				if nRestart > 0:
					self.ModbusThread.join()

				self.ModbusThread.start()
				nRestart = nRestart + 1
				self.ObjmultusdTools.logger.debug("Started Modbus Listening Thread ...  Start #: " + str(nRestart))

			if self.ModbusThread.KeepThreadRunning:
				time.sleep (SleepingTime)

# End Class
#########################################################################
#
# main program
#
def DoTheDeamonJob(bDeamonized = True):

	ObjStatusLED = multusModbusClass()  
	ObjStatusLED.haupt(bDeamonized)

	return

if __name__ == "__main__":

	# Check program must be run as daemon or interactive
	# ( command line parameter -n means interactive )
	bDeamonize = True
	for eachArg in sys.argv:   
		if str(eachArg) == '-n' :
			bDeamonize = False
	 
	if bDeamonize:
		print ("Starting deamonized")

		pid = "/tmp/multusModbus.pid"
		try:
			os.remove(pid)
		except:
			pass
		
		# Daemonize this job
		myname=os.path.basename(sys.argv[0])
		daemon = Daemonize(app=myname, pid=pid, action=DoTheDeamonJob)
		daemon.start()
		
	else:
		print ("Starting in non deamonized mode")
		DoTheDeamonJob (False)
