#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2017-04-12
#
# Nutzung des DO2 als Indikator für Verbindungen
# 
# 0 DO2 Aus:			Prozess läuft nicht oder interner Fehler
# 1 DO2 Blinkt Schnell:	Keine Internet/keien VPn verbindunmg
# 2 DO2 Blinkt langsam:	Internet verbindung keine VPN verbindung
# 3 DO2 An:				Internet verbindung und VPN Verbindung OK
#
##
## 2018-11-12 
## Alles nochmal überarbeitet.. ordentlich gedeaemonized
#
#
# 2019-11-04
# Transformed into a class and fitted it into multus III cocept
#
# 2019-11-28
# changed it from thrift and file stuff to a gRPC Protobuf application
# with direct hardware access
#

import sys
import time
import os
import signal
from daemonize import Daemonize

sys.path.append('/multus/lib')
import libpidfile
import multusdConfig
import multusdTools
import multusdModuleConfig
import NetworkStatus

import libmultusStatusLED

## do the Periodic Alive Stuff
import multusdControlSocketClient

# 2020-06-01
# Json config option
if libmultusStatusLED.UseJsonConfig:
	import libmultusdJson
	import libmultusdJsonModuleConfig


import libmultusdClientBasisStuff

class StatusLEDClass(libmultusdClientBasisStuff.multusdClientBasisStuffClass):

	def __init__(self):

		self.StatusLEDIsRunningTwice = False
		self.ObjmultusdTools = multusdTools.multusdToolsClass()

		## 2020-06-01
		if libmultusStatusLED.UseJsonConfig:
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
			ObjmultusdConfig = multusdConfig.ConfigDataClass()
			ObjmultusdConfig.readConfig()
			
			## after we got the modules init file.. we have to read it, to get the config files for this process
			ObjmultusdModulesConfig = multusdModuleConfig.ClassModuleConfig(ObjmultusdConfig)
			ObjmultusdModulesConfig.ReadModulesConfig()

		#WalkThe list of modules to find our configuration files.. 
		Ident = "multusStatusLED"
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				if libmultusStatusLED.UseJsonConfig:
					self.ObjStatusLEDConfig = libmultusStatusLED.StatusLEDConfigClass(None)
					bSuccess = self.ObjStatusLEDConfig.ReadJsonConfig(self.ObjmultusdTools, self.ObjmultusdConfig, Ident)
					if not bSuccess:
						print ("Error getting Json config, we exit")
						sys.exit(2)
				else:
					self.ObjmultusStatusLEDConfig = libmultusStatusLED.StatusLEDConfigClass(Module.ModuleParameter.ModuleConfig)
					self.ObjmultusStatusLEDConfig.ReadConfig()
					self.ObjmultusStatusLEDConfig.ModuleControlPortEnabled = Module.ModuleParameter.ModuleControlPortEnabled 

				self.ObjmultusStatusLEDConfig.LPIDFile = Module.ModuleParameter.ModulePIDFile
				self.ObjmultusStatusLEDConfig.ModuleControlPort = Module.ModuleParameter.ModuleControlPort 
				# 2021-02-07
				self.ObjmultusStatusLEDConfig.ModuleControlFileEnabled = Module.ModuleParameter.ModuleControlFileEnabled
				self.ObjmultusStatusLEDConfig.ModuleControlMaxAge = Module.ModuleParameter.ModuleControlMaxAge
				break

		self.LogFile = ObjmultusdConfig.LoggingDir +"/" + Module.ModuleParameter.ModuleIdentifier + ".log"
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
			self.StatusLEDIsRunningTwice = False
			print ("We Try to do the PIDFile: " + self.ObjmultusStatusLEDConfig.LPIDFile)
			with(libpidfile.PIDFile(self.ObjmultusStatusLEDConfig.LPIDFile)):
				print ("Writing PID File: " + self.ObjmultusStatusLEDConfig.LPIDFile)
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)
			self.StatusLEDIsRunningTwice = True
			sys.exit(1)

		## get the hardware access
		self.ObjStatusLEDFunctions = libmultusStatusLED.StatusLEDFunctionsClass(self.ObjmultusStatusLEDConfig, self.ObjmultusdTools)
		self.ObjLANWANStatus = NetworkStatus.gRPCLANWANStatusClass(self.ObjmultusdTools)
		self.ObjOVPNStatus = NetworkStatus.gRPCOVPNStatusClass(self.ObjmultusdTools)

		# init parent class
		libmultusdClientBasisStuff.multusdClientBasisStuffClass.__init__(self, self.ObjmultusStatusLEDConfig, self.ObjmultusdTools)
		return

	def __del__(self):
		self.ObjStatusLEDFunctions.LEDOff()

		try:
			if not self.StatusLEDIsRunningTwice:
				os.remove(self.ObjmultusStatusLEDConfig.LPIDFile)
		except:
			ErrorString = self.ObjmultusdTools .FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)

		return


	# Receiving the kill signal, ensure that the heating is off
	def __handler__(self, signum, frame):
		timestr = time.strftime("%Y-%m-%d %H:%M:%S") + " | "

		print (timestr + 'Signal handler called with signal ' + str(signum))
		
		if signum == 15 or signum == 2:
			self.KeepThreadRunning = False

		sys.exit(0)

		return

	############################################################
	###
	### main funtion running the main loop
	###
	def haupt (self, bDaemon):

		## setup the periodic alive mnessage stuff
		bPeriodicmultusdSocketPingEnable = self.ObjmultusStatusLEDConfig.ModuleControlPortEnabled and bDaemon
		## setup the periodic control stuff..
		## if this does not succeed .. we do not have to continue
		SleepingTime, self.KeepThreadRunning = self.SetupPeriodicmessages(bPeriodicmultusdSocketPingEnable)
	
	
		## 2021-02-14
		## Made it a bit better
		## Dfine some Constants
		ConnectionStatus_Worst_Ever = 0
		Connection_Status_No_Internet = 1
		Connection_Status_Internet_No_OVPN = 2
		Connection_Status_Internet_OVPN = 3

		LEDStatus = False
		ConnectionStatus = ConnectionStatus_Worst_Ever
		OldConnectionStatus = ConnectionStatus
		Counter = 0
		MaxConnectionErrorCounter = 3
		RefreshCounter = 0
		MaxRefreshRounter = 120
		iErrors = -1
		vErrors = -1

		StartupDelay = 70.0
		CheckInterval = 20.0
		TimeNextInternetCheck = time.time() + StartupDelay - 2.0
		TimeNextOVPNCheck = time.time() + StartupDelay + 2.0
		 
		while (self.KeepThreadRunning):
			
			## We do the periodic messages and stuff to indicate that we are alive for the multusd
			self.KeepThreadRunning = self.DoPeriodicMessage(bPeriodicmultusdSocketPingEnable)

			Timestamp = time.time()

			#read Errors Internet connection
			if self.ObjmultusStatusLEDConfig.LEDInternetEnable and Timestamp > TimeNextInternetCheck:
				LocalLANWANStatus, bConnectionStatus = self.ObjLANWANStatus.GetWANStatus("StatusLED WAN Status Request")
				TimeNextInternetCheck = Timestamp + CheckInterval
				if not LocalLANWANStatus.ValidStatus:
					iErrors = -1
				elif not LocalLANWANStatus.ConnectionStatus:
					iErrors = 1
				elif LocalLANWANStatus.ConnectionStatus:
					iErrors = 0
			elif not self.ObjmultusStatusLEDConfig.LEDInternetEnable:
				iErrors = 0
				

			if self.ObjmultusStatusLEDConfig.LEDVPNEnable and Timestamp > TimeNextOVPNCheck:
				LocalOVPNStatus, bConnectionStatus = self.ObjOVPNStatus.GetOVPNStatus("StatusLED OVPN Status Request")
				TimeNextOVPNCheck = Timestamp + CheckInterval
				if not LocalOVPNStatus.ValidStatus:
					vErrors = -1
				elif not LocalOVPNStatus.ConnectionStatus:
					vErrors = 1
				elif LocalOVPNStatus.ConnectionStatus:
					vErrors = 0
			elif not self.ObjmultusStatusLEDConfig.LEDVPNEnable:
				## if no OVPN Check is done.. the status shall be OK
				vErrors = 0

			print ("InternetErrors: " + str(iErrors))
			print ("OpenVPNErrors:  " + str(vErrors))

			# 2021-02-14
			# made it less worse... this old programm
			#
			# ConnectionStatus_Worst_Ever = 0
			# Connection_Status_No_Internet = 1
			# Connection_Status_Internet_No_OVPN = 2
			# Connection_Status_Internet_OVPN = 3

			## We got nothing .. no internet and no VPN
			## complete desaster
			if iErrors < 0:
				ConnectionStatus = ConnectionStatus_Worst_Ever

			## Everything is OK.. Internet fine as well as OVPN
			elif iErrors == 0 and vErrors == 0:
				ConnectionStatus = Connection_Status_Internet_OVPN

			## Almost OK.. Internet OK, but OVPN on failure
			elif iErrors == 0 and vErrors != 0:
				ConnectionStatus = Connection_Status_Internet_No_OVPN

			## Internet Errore
			elif iErrors > 0:	
				ConnectionStatus = Connection_Status_No_Internet

			if ConnectionStatus == ConnectionStatus_Worst_Ever:
				Counter = 0
				LEDStatus = self.ObjStatusLEDFunctions.LEDOff()

			elif ConnectionStatus == Connection_Status_No_Internet:
				if LEDStatus:
					Counter = 0
					LEDStatus = self.ObjStatusLEDFunctions.LEDOff()
				else:
					Counter = 0
					LEDStatus = self.ObjStatusLEDFunctions.LEDOn()

			elif ConnectionStatus == Connection_Status_Internet_No_OVPN:

				if LEDStatus and Counter >= MaxConnectionErrorCounter:
					Counter = 0
					LEDStatus = self.ObjStatusLEDFunctions.LEDOff()
				elif not LEDStatus and Counter >= MaxConnectionErrorCounter:
					Counter = 0
					LEDStatus = self.ObjStatusLEDFunctions.LEDOn()

			elif ConnectionStatus == Connection_Status_Internet_OVPN:
				Counter = 0
				if not LEDStatus or RefreshCounter >= MaxRefreshRounter:
					RefreshCounter = 0	
					LEDStatus = self.ObjStatusLEDFunctions.LEDOn()

			## 2021-02-14
			## do some logging
			if OldConnectionStatus != ConnectionStatus:

				## Ok, we go through it again.. but it does not matter in this tiny process
				if ConnectionStatus == ConnectionStatus_Worst_Ever:
					self.ObjmultusdTools.logger.debug("ConnectionStatus changed: Something seriously wrong....")
					
				elif ConnectionStatus == Connection_Status_No_Internet:
					self.ObjmultusdTools.logger.debug("ConnectionStatus changed: No Internet")

				elif ConnectionStatus == Connection_Status_Internet_No_OVPN:
					self.ObjmultusdTools.logger.debug("ConnectionStatus changed: Internet OK but no OpenVPN")

				elif ConnectionStatus == Connection_Status_Internet_OVPN:

					if not self.ObjmultusStatusLEDConfig.LEDVPNEnable:
						self.ObjmultusdTools.logger.debug("ConnectionStatus changed: Internet OK -- OpenVPN is not evaluated.. we regard it as OK")
					else:
						self.ObjmultusdTools.logger.debug("ConnectionStatus changed: Internet OK as well as OpenVPN OK .. everything is fine")

				## we log once.. we keep it in mind
				OldConnectionStatus = ConnectionStatus

		
			## Damit ab und zu das LED-Signal aktualisiert wird
			## Der thrift-Prozess koennte ja neu gestartet sein
			RefreshCounter += 1

			Counter += 1
			time.sleep (SleepingTime)

def DoTheDeamonJob(bDaemon = True):

	ObjStatusLED = StatusLEDClass()  
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
		print ("Starten im deamonize modus")

		pid = "/tmp/dummy.pid"
		
		# Daemonize this job
		myname=os.path.basename(sys.argv[0])
		daemon = Daemonize(app=myname, pid=pid, action=DoTheDeamonJob)
		daemon.start()
		
	else:
		print ("Starten im consolen modus")
		DoTheDeamonJob (False)
