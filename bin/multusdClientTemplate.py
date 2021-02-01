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
# changed it to a process which also could be executed multiple times
# 2019-12-30

import sys
import time
import os
import signal
import tempfile

from daemonize import Daemonize

sys.path.append('/multus/lib')
import libpidfile
import multusdTools
import multusdConfig
import multusdModuleConfig

# the multusd fail-safe functions, the config and the main operations of this process
import libmultusdClientTemplate

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 2020-06-01
# Json config option
if libmultusdClientTemplate.UseJsonConfig:
	import libmultusdJson
	import libmultusdJsonModuleConfig

## 2019-12-30
## We want to run more, then just 1 instace of each process
## made it possible

class multusdClientTemplateClass(object):

	def __init__(self):
		RunOnce = True

		ScriptName = os.path.basename(__file__)
		print ("Filename: " + ScriptName)
		## 2019-12-30
		## We try to get the Instance .. if there is one
		FirstPart = ScriptName.split('.')
		StrInstance = FirstPart[0].split('_')
		print ("StrInstance: " + str(StrInstance))
		
		Instance = 0
		if len(StrInstance) > 1 and StrInstance[1].isnumeric():
			RunOnce = False
			Instance = int(StrInstance[1])

		self.ObjmultusdTools = multusdTools.multusdToolsClass()
		
		## 2020-06-01
		if libmultusdClientTemplate.UseJsonConfig:
			# first we get the config of the multusd system
			self.ObjmultusdConfig = libmultusdJson.multusdJsonConfigClass(ObjmultusdTools = self.ObjmultusdTools)
			self.ObjmultusdConfig.ReadConfig()
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
		self.ModuleControlPort = 43000

		#WalkThe list of modules to find our configuration files.. 
		BasicIdent = "multusdClientTemplate"
		Ident = BasicIdent
		if not RunOnce:
			Ident = Ident + "_" + StrInstance[1]

		for Module in ObjmultusdModulesConfig.AllModules:
			print ("Searching for our config: Checking module Ident: " + Module.ModuleParameter.ModuleIdentifier + " against our own Ident: " + Ident)
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				print ("YYYYYY Got it")
				if libmultusdClientTemplate.UseJsonConfig:
					self.ObjmultusdClientTemplateConfig = libmultusdClientTemplate.multusdClientTemplateConfigClass(None)
					self.ObjmultusdClientTemplateConfig.Instance = Instance
					bSuccess = self.ObjmultusdClientTemplateConfig.ReadJsonConfig(self.ObjmultusdTools, self.ObjmultusdConfig, BasicIdent, Instance)
					if not bSuccess:
						print ("Error getting Json config, we exit")
						sys.exit(2)
				else:
					self.ObjmultusdClientTemplateConfig = libmultusdClientTemplate.multusdClientTemplateConfigClass(Module.ModuleParameter.ModuleConfig)
					self.ObjmultusdClientTemplateConfig.Instance = Instance
					self.ObjmultusdClientTemplateConfig.ReadConfig()
					self.ObjmultusdClientTemplateConfig.ModuleControlPortEnabled = Module.ModuleParameter.ModuleControlPortEnabled 

				self.ObjmultusdClientTemplateConfig.Ident = Ident
				self.ModuleControlPort = Module.ModuleParameter.ModuleControlPort 
				
				## 2021-01-31 .. extended it by the PID file control
				self.ObjmultusdClientTemplateConfig.LPIDFile = Module.ModuleParameter.ModulePIDFile
				self.ObjmultusdClientTemplateConfig.ModuleControlFileEnabled = Module.ModuleParameter.ModuleControlFileEnabled 
				self.ObjmultusdClientTemplateConfig.ModuleControlMaxAge = Module.ModuleParameter.ModuleControlMaxAge
				## end modification

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
			print ("We Try to do the PIDFile: " + self.ObjmultusdClientTemplateConfig.LPIDFile)
			with(libpidfile.PIDFile(self.ObjmultusdClientTemplateConfig.LPIDFile)):
				print ("Writing PID File: " + self.ObjmultusdClientTemplateConfig.LPIDFile)
			self.ProcessIsRunningTwice = False
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString + " PIDFile: " + self.ObjmultusdClientTemplateConfig.LPIDFile)
			sys.exit(1)

		self.ObjmultusdTools.logger.debug("Started up.. initializing finished")

		return

	def __del__(self):
		try:
			if not self.ProcessIsRunningTwice:
				os.remove(self.ObjmultusdClientTemplateConfig.LPIDFile)
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
			self.ObjmultusdClientTemplateOperate.KeepThreadRunning = False
			

	def haupt (self, bDaemon):

		PercentageOff = 80.0 
		multusdPingInterval = self.ObjmultusdClientTemplateConfig.ModuleControlMaxAge - (self.ObjmultusdClientTemplateConfig.ModuleControlMaxAge * PercentageOff/100.0)
		print ("multus Ping Interval: " + str(multusdPingInterval))

		self.ObjmultusdClientTemplateOperate = libmultusdClientTemplate.multusdClientTemplateOperateClass(self.ObjmultusdClientTemplateConfig, self.ObjmultusdTools)
		self.ObjmultusdClientTemplateOperate.Operate(multusdPingInterval, bDaemon and self.ObjmultusdClientTemplateConfig.ModuleControlPortEnabled, self.ModuleControlPort)

		print ("Exiting multusdClientTemplate Main-Program")

# End Class
#########################################################################
#
# main program
#
def DoTheDeamonJob(bDaemon = True):

	ObjStatusLED = multusdClientTemplateClass()  
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

		## We build a stupid temp-filename
		tf = tempfile.NamedTemporaryFile(prefix="DaemonPID")
		pid = tf.name
	
		print ("We use stupid PID-File: " + pid)

		"""
		try:
			os.remove("/tmp/DaemonPID*")
		except:
			pass
		"""

		# Daemonize this job
		myname=os.path.basename(sys.argv[0])
		daemon = Daemonize(app=myname, pid=pid, action=DoTheDeamonJob)
		daemon.start()
		
	else:
		print ("Starting in non deamonized mode")
		DoTheDeamonJob (False)
