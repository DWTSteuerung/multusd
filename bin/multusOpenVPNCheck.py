#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Karl Keusgen
# Do all the networking stuff..
#
# 2019-11-24
# Today we want to start with some easy internet checking an 
# providing the result of the internet checking via gRPC
# my first google protobuf and gRPC application
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
import libOpenVPNCheck

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 2020-06-01
# Json config option
if libOpenVPNCheck.UseJsonConfig:
	import libmultusdJson
	import libmultusdJsonModuleConfig

class multusOVPNClass(object):
	def __init__(self):
		self.ObjmultusdTools = multusdTools.multusdToolsClass()

		## 2020-06-01
		if libOpenVPNCheck.UseJsonConfig:
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
		multusIntegrityEnabled = False
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == "multusIntegrity" and Module.ModuleParameter.Enabled:
				multusIntegrityEnabled = True
				print ("DSVIntegrity is enabled")
				break

		#WalkThe list of modules to find our configuration files.. 
		Ident = "OpenVPNCheck"
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				if libOpenVPNCheck.UseJsonConfig:
					self.ObjmultusOpenVPNCheckConfig = libOpenVPNCheck.multusOVPNConfigClass(None)
					bSuccess = self.ObjmultusOpenVPNCheckConfig.ReadJsonConfig(self.ObjmultusdTools, self.ObjmultusdConfig, Ident)
					if not bSuccess:
						print ("Error getting Json config, we exit")
						sys.exit(2)
				else:
					self.ObjmultusOpenVPNCheckConfig = libOpenVPNCheck.multusOVPNConfigClass(Module.ModuleParameter.ModuleConfig)
					self.ObjmultusOpenVPNCheckConfig.ReadConfig()
					self.ObjmultusOpenVPNCheckConfig.ModuleControlPortEnabled = Module.ModuleParameter.ModuleControlPortEnabled 

				self.ObjmultusOpenVPNCheckConfig.Ident = Ident
				self.ObjmultusOpenVPNCheckConfig.multusIntegrityEnabled = multusIntegrityEnabled
				self.ObjmultusOpenVPNCheckConfig.LPIDFile = Module.ModuleParameter.ModulePIDFile
				self.ObjmultusOpenVPNCheckConfig.ModuleControlPort = Module.ModuleParameter.ModuleControlPort 
				self.ObjmultusOpenVPNCheckConfig.ModuleControlMaxAge = Module.ModuleParameter.ModuleControlMaxAge
				# 2021-02-07
				self.ObjmultusOpenVPNCheckConfig.ModuleControlFileEnabled = Module.ModuleParameter.ModuleControlFileEnabled
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
			print ("We Try to do the PIDFile: " + self.ObjmultusOpenVPNCheckConfig.LPIDFile)
			with(libpidfile.PIDFile(self.ObjmultusOpenVPNCheckConfig.LPIDFile)):
				print ("Writing PID File: " + self.ObjmultusOpenVPNCheckConfig.LPIDFile)

			self.ProcessIsRunningTwice = False
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString + " PIDFile: " + self.ObjmultusOpenVPNCheckConfig.LPIDFile)
			sys.exit(1)	

		self.ObjmultusdTools.logger.debug("Started up.. initializing finished")

		return

	def __del__(self):
		try:
			if not self.ProcessIsRunningTwice:
				os.remove(self.ObjmultusOpenVPNCheckConfig.LPIDFile)
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)
 

	# Receiving the kill signal, ensure that the heating is off
	def __handler__(self, signum, frame):
		timestr = time.strftime("%Y-%m-%d %H:%M:%S") + " | "

		print (timestr + 'Signal handler called with signal ' + str(signum))
		
		if signum == 15 or signum == 2:
			## Stop the loop in the server and close the gRPC Socket
			self.OVPNCheckServer.KeepThreadRunning = False
			self.OVPNCheckServer.gRPCServer.stop(0)

			sys.exit(0)

	def haupt (self, bDaemon):
		
		self.OVPNCheckServer = libOpenVPNCheck.gRPCOperateClass(self.ObjmultusOpenVPNCheckConfig, self.ObjmultusdTools)
		self.OVPNCheckServer.RungRPCServer(bDaemon and self.ObjmultusOpenVPNCheckConfig.ModuleControlPortEnabled)

		self.ObjmultusdTools.logger.debug(" Stopped")
	
		return

# End Class
#########################################################################
#
# main program
#
def DoTheDeamonJob(bDaemon = True):

	ObjStatusLED = multusOVPNClass()  
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

		pid = "/tmp/multusOVPN.pid"
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
