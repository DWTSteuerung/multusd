#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Karl Keusgen
# template and example of multusd integrarted process
#
# 2019-11-15
#
# complete rework
# 2019-12-08
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

# the multusd fail-safe functions, the config and the main operations of this process
import libmultusReadDIDO

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 2020-06-01
# Json config option
if libmultusReadDIDO.UseJsonConfig:
	import libmultusdJson
	import libmultusdJsonModuleConfig

class multusReadDIDOClass(object):

	def __init__(self):
		self.ObjmultusdTools = multusdTools.multusdToolsClass()

		## 2020-06-01
		if libmultusReadDIDO.UseJsonConfig:
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
		Ident = "multusReadDIDO"
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				if libmultusReadDIDO.UseJsonConfig:
					self.ObjmultusReadDIDOConfig = libmultusReadDIDO.multusReadDIDOConfigClass(None)
					bSuccess = self.ObjmultusReadDIDOConfig.ReadJsonConfig(self.ObjmultusdTools, self.ObjmultusdConfig, Ident)
					if not bSuccess:
						print ("Error getting Json config, we exit")
						sys.exit(2)
				else:
					self.ObjmultusReadDIDOConfig = libmultusReadDIDO.multusReadDIDOConfigClass(Module.ModuleParameter.ModuleConfig)
					self.ObjmultusReadDIDOConfig.ReadConfig()
					self.ObjmultusReadDIDOConfig.ModuleControlPortEnabled = Module.ModuleParameter.ModuleControlPortEnabled 

				self.ObjmultusReadDIDOConfig.Ident = Ident
				self.ObjmultusReadDIDOConfig.LPIDFile = Module.ModuleParameter.ModulePIDFile
				self.ObjmultusReadDIDOConfig.ModuleControlPort = Module.ModuleParameter.ModuleControlPort 
				self.ObjmultusReadDIDOConfig.ModuleControlMaxAge = Module.ModuleParameter.ModuleControlMaxAge
				# 2021-02-07
				self.ObjmultusReadDIDOConfig.ModuleControlFileEnabled = Module.ModuleParameter.ModuleControlFileEnabled
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
			print ("We Try to do the PIDFile: " + self.ObjmultusReadDIDOConfig.LPIDFile)
			with(libpidfile.PIDFile(self.ObjmultusReadDIDOConfig.LPIDFile)):
				print ("Writing PID File: " + self.ObjmultusReadDIDOConfig.LPIDFile)
			self.ProcessIsRunningTwice = False
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString + " PIDFile: " + self.ObjmultusReadDIDOConfig.LPIDFile)
			sys.exit(1)

		self.ObjmultusdTools.logger.debug("Started up.. initializing finished")

		return

	def __del__(self):
		try:
			if not self.ProcessIsRunningTwice:
				os.remove(self.ObjmultusReadDIDOConfig.LPIDFile)
		except:
			ErrorString = self.ObjmultusdTools .FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)

		self.ObjmultusdTools.logger.debug("Stopped")

		return

	# Receiving the kill signal, ensure that the heating is off
	def __handler__(self, signum, frame):
		timestr = time.strftime("%Y-%m-%d %H:%M:%S") + " | "

		print (timestr + 'Signal handler called with signal ' + str(signum))
		
		if signum == 15 or signum == 2:
			self.ObjmultusReadDIDOOperate.KeepThreadRunning = False
			

	def haupt (self, bDaemon):

		self.ObjmultusReadDIDOOperate = libmultusReadDIDO.multusReadDIDOOperateClass(self.ObjmultusReadDIDOConfig, self.ObjmultusdTools)
		self.ObjmultusReadDIDOOperate.Operate(bDaemon and self.ObjmultusReadDIDOConfig.ModuleControlPortEnabled)

		print ("Exiting multusReadDIDO Main-Program")

# End Class
#########################################################################
#
# main program
#
def DoTheDeamonJob(bDaemon = True):

	ObjStatusLED = multusReadDIDOClass()  
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

		pid = "/tmp/multusReadDIDO.pid"
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
