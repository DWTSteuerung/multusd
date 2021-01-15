# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2019-12-08
#
# After changing the FailSafe technology 
#
import os
import sys
import time
import configparser

sys.path.append('/multus/lib')
## do the Periodic Alive Stuff
import multusdControlSocketClient
import multusdBasicConfigfileStuff

# 2020-06-01
# Json config option
import libUseJsonConfig
UseJsonConfig = libUseJsonConfig.UseJsonConfig
import urllib.request
import json

############################################################################################################
#
# 2019-12-07
# Class to be called by multusdService
# it is mandatory for each native multusd process, who uses the controlPort function
# to have a class like this
#
class FailSafeClass(object):
	def __init__(self, Tools, ModuleConfig, Ident, dBNKEnabled):
		
		self.Ident = Ident
		
		return

	def SetIntoFailSafeState(self, ProcessIsRunning):

		return

	def ExecuteAfterStop(self, ProcessIsRunning):

		return

	def ExecuteAfterStart(self, ProcessIsRunning):

		return

	def ExecutePeriodic(self, ProcessIsRunning):

		return
############################################################################################################

class multusdClientTemplateConfigClass(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):
	def __init__(self, ConfigFile):
		## initialize the parent class
		multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		self.ConfigFile = ConfigFile
		self.SoftwareVersion = "1"
	
		return

	def ReadConfig(self):
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden == True:
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')
			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))

		else:

			print ("No config file .. exiting")
			return False

		print ("multusdClientTemplate started with these parameters")
		print ("multusdClientTemplate : " + str(self.ConfigVersion))
		
		return True

	# 2020-06-01	
	def ReadJsonConfig(self, ObjmultusdTools, ObjmultusdJsonConfig, Ident, Instance = 0):
		bSuccess = False
		try: 
			Timeout = 5
			url = ObjmultusdJsonConfig.JsonSingleModuleURL + Ident
			print ("We get the Json process config form url: " + url)
			with urllib.request.urlopen(url , timeout = Timeout) as url:
				ConfigData = json.loads(url.read().decode())

			#print (ConfigData)
			for (ModuleKey, ModuleValue) in ConfigData.items():
				if ModuleKey == "Instances":
					# We walk through the instaces looking for the required one	
					InstanceCounter = 0
					for SingleInstance in ModuleValue:
						if InstanceCounter == Instance:
							print ("We found the parameters of this process: " + str(SingleInstance))
							self.ConfigVersion = SingleInstance['ConfigVersion']
							self.DummyParam = SingleInstance['DummyParam']
							break

						InstanceCounter += 1

			bSuccess = True
		except:
			ErrorString = ObjmultusdTools.FormatException()
			LogString = "Read in Json Process config failed with Error: " + ErrorString
			print(LogString)
			
		return bSuccess

############################################################################################################

class multusdClientTemplateOperateClass(object):
	def __init__(self, ObjmultusdClientTemplateConfig, ObjmultusdTools):

		self.ObjmultusdClientTemplateConfig = ObjmultusdClientTemplateConfig
		self.ObjmultusdTools = ObjmultusdTools

		self.KeepThreadRunning = True
		
		return

############################################################
	def __del__(self):
		print ("leaving multusdClientTemplateOperateClass")
		pass

############################################################
	def DoPeriodicMessage(self):
		if self.periodic:
			Timestamp = time.time()
			if Timestamp >= self.TimestampNextmultusdPing:
				self.periodic.SendPeriodicMessage()
				self.TimestampNextmultusdPing = time.time() + self.multusdPingInterval
				
			if self.periodic.WeAreOnError:
				self.ObjmultusdTools.logger.debug("Error connecting to multusd... we stop running")
				self.KeepThreadRunning = False
		return 

############################################################
	def Operate(self, multusdPingInterval, bPeriodicEnable, ModuleControlPort):
		self.multusdPingInterval = multusdPingInterval
		## setup the periodic alive mnessage stuff
		self.periodic = None
		if bPeriodicEnable:
			print ("Setup the periodic Alive messages")
			self.TimestampNextmultusdPing = time.time()
			self.periodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', ModuleControlPort)
			if not self.periodic.ConnectFeedbackSocket():
				self.ObjmultusdTools.logger.debug("Stopping Process, cannot establish Feedback Connection to multusd")
				sys.exit(1)

		# 2020-01-01
		# the loop shall not sleep longer than 1 second.. otherwise the handling in the stop procedure gets too slow
		SleepingTime = multusdPingInterval
		if multusdPingInterval > 1.0:
			SleepingTime = 1.0

		while self.KeepThreadRunning:
			
			self.DoPeriodicMessage()
			
			## place your code for individual actions here
			
			if self.KeepThreadRunning:
				time.sleep (SleepingTime)

		return
