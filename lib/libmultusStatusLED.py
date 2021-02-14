# -*- coding: utf-8 -*-
#
# providing functions and config to the
# status-led Process and the multusd.. the multusd for switching the Status LED off when stopping the process
#
# 2019-11-30
# Karl Keusgen
#
import os
import configparser
import sys
import time

sys.path.append('/multus/lib')
import DWTThriftConfig3
import multusHardwareHandler

# 2020-06-01
# Json config option
import libUseJsonConfig
UseJsonConfig = libUseJsonConfig.UseJsonConfig
import urllib.request
############################################################################################################
#
# 2019-12-07
# Class to be called by multusdService
# it is mandatory for each native multusd process, who uses the controlPort function
# to have a class like this
#
class FailSafeClass(object):
	def __init__(self, Tools, ModuleConfig, Ident, multusIntegrityEnabled):
		
		self.Ident = Ident

		ObjmultusStatusLEDConfig = StatusLEDConfigClass(ModuleConfig)
		ObjmultusStatusLEDConfig.ReadConfig()

		self.ObjmultusStatusLEDFunctions = StatusLEDFunctionsClass(ObjmultusStatusLEDConfig, Tools)
		return

	def SetIntoFailSafeState(self, ProcessIsRunning):
		self.ObjmultusStatusLEDFunctions.LEDOff() 
		return

	def ExecuteAfterStop(self, ProcessIsRunning):

		return

	def ExecuteAfterStart(self, ProcessIsRunning):

		return

	def ExecutePeriodic(self, ProcessIsRunning):

		return
############################################################################################################


class StatusLEDConfigClass(DWTThriftConfig3.ConfigDataClass):
	def __init__(self, ConfigFile):
		## initialize the parent class
		DWTThriftConfig3.ConfigDataClass.__init__(self)
		self.ConfigFile = ConfigFile
		self.LEDInternetEnable = None
		self.LEDVPNEnable = None
		self.OutputPIN = None

		# 2021-02-07
		self.SoftwareVersion = "1"
		
		self.ModuleControlPortEnabled = True
		self.ModuleControlFileEnabled = False
		self.ModuleControlPort = 43000

		return

	####################################################################
	def ReadConfig(self):
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden == True:
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')

			self.SoftwareVersion = "1"
			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))
			self.LEDInternetEnable = self.__assignBool__(config.get('InternetLED', 'Value'))
			self.LEDVPNEnable = self.__assignBool__(config.get('OpenVPNLED', 'Value'))
			self.OutputPIN = self.__assignInt__(config.get('OutputPIN', 'Value'))
		else:

			print ("No config file .. exiting")
			return False

		print ("LED Indication started with these parameters")
		print ("LED Internet Enable: " + str(self.LEDInternetEnable))
		print ("LED VPN Enable: " + str(self.LEDVPNEnable))
		
		return True

class StatusLEDFunctionsClass(object):
	def __init__(self, ObjmultusStatusLEDConfig, ObjmultusdTools):
		
		self.ObjmultusStatusLEDConfig = ObjmultusStatusLEDConfig
		self.ObjmultusdTools = ObjmultusdTools
	
		## get the hardware access
		self.ObjmultusHardware = multusHardwareHandler.multusHardwareHandlerClass(self.ObjmultusStatusLEDConfig, self.ObjmultusdTools)
		self.DOSet = self.ObjmultusHardware.InitDOSet()
		return


	def LEDOn (self):

		self.DOSet[self.ObjmultusStatusLEDConfig.OutputPIN - 1] = 0
		self.ObjmultusHardware.writeDO (0, self.DOSet) 

		timestr = time.strftime("%Y-%m-%d %H:%M:%S") + " | "
		print (timestr + "LED on")

		return True

	def LEDOff (self):
		self.DOSet[self.ObjmultusStatusLEDConfig.OutputPIN - 1] = 1
		self.ObjmultusHardware.writeDO (0, self.DOSet) 

		timestr = time.strftime("%Y-%m-%d %H:%M:%S") + " | "
		print (timestr + "LED off")

		return False


