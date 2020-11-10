#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Karl Keusgen
# Runs a single OpenVPN Client.. 
#
# 2019-12-30
#

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
import libmultusOVPNClient

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

## 2019-12-30
## We want to run more, then just 1 instace of each process
## made it possible

# 2020-06-01
# Json config option

if libmultusOVPNClient.UseJsonConfig:
	import libmultusdJson
	import libmultusdJsonModuleConfig

class multusOVPNClientClass(object):

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
		if libmultusOVPNClient.UseJsonConfig:
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
		self.ModuleControlPort = 43000
		self.ModuleControlPortEnabled = True

		#WalkThe list of modules to find our configuration files.. 
		BasicIdent = "multusOVPNClient"
		Ident = BasicIdent
		if not RunOnce:
			Ident = Ident + "_" + StrInstance[1]

		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				if libmultusOVPNClient.UseJsonConfig:
					self.ObjmultusOVPNClientConfig = libmultusOVPNClient.multusOVPNClientConfigClass(None)
					bSuccess = self.ObjmultusOVPNClientConfig.ReadJsonConfig(self.ObjmultusdTools, self.ObjmultusdConfig, BasicIdent, Instance)
					if not bSuccess:
						print ("Error getting Json config, we exit")
						sys.exit(2)
				else:
					self.ObjmultusOVPNClientConfig = libmultusOVPNClient.multusOVPNClientConfigClass(Module.ModuleParameter.ModuleConfig)
					self.ObjmultusOVPNClientConfig.ReadConfig()
					self.ModuleControlPortEnabled = Module.ModuleParameter.ModuleControlPortEnabled 

				self.ObjmultusOVPNClientConfig.Ident = Ident
				self.LPIDFile = Module.ModuleParameter.ModulePIDFile
				self.ModuleControlPort = Module.ModuleParameter.ModuleControlPort 
				self.ModuleControlMaxAge = Module.ModuleParameter.ModuleControlMaxAge
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
			print ("We Try to do the PIDFile: " + self.LPIDFile)
			with(libpidfile.PIDFile(self.LPIDFile)):
				print ("Writing PID File: " + self.LPIDFile)
			self.ProcessIsRunningTwice = False
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString + " PIDFile: " + self.LPIDFile)
			sys.exit(1)

		self.ObjmultusdTools.logger.debug("Started up.. initializing finished")

		return

	def __del__(self):
		try:
			if not self.ProcessIsRunningTwice:
				os.remove(self.LPIDFile)
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
			self.ObjmultusOVPNClientOperate.KeepThreadRunning = False
			

	def haupt (self, bDaemon):

		PercentageOff = 80.0 
		multusdPingInterval = self.ModuleControlMaxAge - (self.ModuleControlMaxAge * PercentageOff/100.0)
		print ("multus Ping Interval: " + str(multusdPingInterval))

		self.ObjmultusOVPNClientOperate = libmultusOVPNClient.multusOVPNClientOperateClass(self.ObjmultusOVPNClientConfig, self.ObjmultusdTools)
		self.ObjmultusOVPNClientOperate.RungRPCServer(multusdPingInterval, bDaemon and self.ModuleControlPortEnabled, self.ModuleControlPort)

		print ("Exiting multusOVPNClient Main-Program")

# End Class
#########################################################################
#
# main program
#
def DoTheDeamonJob(bDaemon = True):

	ObjStatusLED = multusOVPNClientClass()  
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
