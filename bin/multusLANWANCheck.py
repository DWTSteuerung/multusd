#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-
#
# Karl Keusgen
# Do all the networking stuff..
#
# 2019-11-24
# Today we want to start with some easy internet checking an 
# providing the result of the internet checking via gRPC
# my first google protobuf and gRPC application
#
# 2019-12-31
# detached the LANWAN Check funtionality from the multusLAN process
#

import sys
import time
import os
import signal

from daemonize import Daemonize

import configparser

sys.path.append('/multus/lib')
import libpidfile
import multusdTools
import multusdConfig
import multusdModuleConfig

## do the Periodic Alive Stuff
import multusdControlSocketClient
import libmultusLANWANCheck

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 2020-06-01
# Json config option
if libmultusLANWANCheck.UseJsonConfig:
	import libmultusdJson
	import libmultusdJsonModuleConfig

class multusLANWANCheckClass(object):
	def __init__(self):
		self.ObjmultusdTools = multusdTools.multusdToolsClass()

		## 2020-06-01
		if libmultusLANWANCheck.UseJsonConfig:
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

		# First we check, whether the DSVIntegrity is enabled
		DSVIntegrityEnabled = False
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == "DSVIntegrity" and Module.ModuleParameter.Enabled:
				DSVIntegrityEnabled = True
				break

		#WalkThe list of modules to find our configuration files.. 
		Ident = "multusLANWANCheck"
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				if libmultusLANWANCheck.UseJsonConfig:
					self.ObjmultusLANWANCheckConfig = libmultusLANWANCheck.multusLANWANCheckConfigClass(None)
					bSuccess = self.ObjmultusLANWANCheckConfig.ReadJsonConfig(self.ObjmultusdTools, self.ObjmultusdConfig, Ident)
					if not bSuccess:
						print ("Error getting Json config, we exit")
						sys.exit(2)
				else:
					self.ObjmultusLANWANCheckConfig = libmultusLANWANCheck.multusLANWANCheckConfigClass(Module.ModuleParameter.ModuleConfig)
					self.ObjmultusLANWANCheckConfig.ReadConfig()
					self.ModuleControlPortEnabled = Module.ModuleParameter.ModuleControlPortEnabled 

				self.ObjmultusLANWANCheckConfig.Ident = Ident
				self.ObjmultusLANWANCheckConfig.DSVIntegrityEnabled = DSVIntegrityEnabled 
				self.ObjmultusLANWANCheckConfig.LPIDFile = Module.ModuleParameter.ModulePIDFile
				self.ObjmultusLANWANCheckConfig.ModuleControlPort = Module.ModuleParameter.ModuleControlPort 
				self.ObjmultusLANWANCheckConfig.ModuleControlMaxAge = Module.ModuleParameter.ModuleControlMaxAge
				# 2021-02-07
				self.ObjmultusLANWANCheckConfig.ModuleControlFileEnabled = Module.ModuleParameter.ModuleControlFileEnabled
				break

	
		self.LogFile = self.ObjmultusdConfig.LoggingDir +"/" + Module.ModuleParameter.ModuleIdentifier + ".log"
		if self.LogFile:
			## We initialize logging
			self.ObjmultusdTools.InitGlobalLogging(self.LogFile)
		else:
			self.ObjmultusdTools.InitGlobalLogging("/dev/null")

		# Signal handler initialisieren
		signal.signal(signal.SIGTERM, self.__handler__)
		signal.signal(signal.SIGINT, self.__handler__)

		## Do the PIDFIle
		try:
			print ("We Try to do the PIDFile: " + self.ObjmultusLANWANCheckConfig.LPIDFile)
			with(libpidfile.PIDFile(self.ObjmultusLANWANCheckConfig.LPIDFile)):
				print ("Writing PID File: " + self.ObjmultusLANWANCheckConfig.LPIDFile)

			self.ProcessIsRunningTwice = False
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString + " PIDFile: " + self.ObjmultusLANWANCheckConfig.LPIDFile)
			sys.exit(1)	

		self.ObjmultusdTools.logger.debug("Started up.. initializing finished")

		return

	def __del__(self):
		try:
			if not self.ProcessIsRunningTwice:
				os.remove(self.ObjmultusLANWANCheckConfig.LPIDFile)
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)
 

	# Receiving the kill signal, ensure that the heating is off
	def __handler__(self, signum, frame):
		timestr = time.strftime("%Y-%m-%d %H:%M:%S") + " | "

		print (timestr + 'Signal handler called with signal ' + str(signum))
		
		if signum == 15 or signum == 2:
			## Stop the loop in the server and close the gRPC Socket
			self.LANWANCheckServer.KeepThreadRunning = False
			self.LANWANCheckServer.gRPCServer.stop(0)

			sys.exit(0)

	def haupt (self, bDaemon):
		
		self.LANWANCheckServer = libmultusLANWANCheck.gRPCOperateClass(self.ObjmultusLANWANCheckConfig, self.ObjmultusdTools)
		self.LANWANCheckServer.RungRPCServer(bDaemon and self.ObjmultusLANWANCheckConfig.ModuleControlPortEnabled)

		self.ObjmultusdTools.logger.debug(" Stopped")
	
		return

# End Class
#########################################################################
#
# main program
#
def DoTheDeamonJob(bDaemon = True):

	ObjStatusLED = multusLANWANCheckClass()  
	ObjStatusLED.haupt(bDaemon)

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

		pid = "/tmp/multusLANWANCheck.pid"
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
