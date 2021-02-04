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
# the failsafe class will be loaded and executed, if the Process check is done by the control port option
# the other checks like check by PID file timstamp or kill 0 can be used simultaniously and sometimes it is necessarry to have more then 
# just one method of process check
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
		
		self.ModuleControlPortEnabled = True
		self.ModuleControlFileEnabled = False
		self.ModuleControlPort = 43000

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
###
### The main Class, weher all jobs are done
### 
class multusdClientTemplateOperateClass(object):
	def __init__(self, ObjmultusdClientTemplateConfig, ObjmultusdTools):

		self.ObjmultusdClientTemplateConfig = ObjmultusdClientTemplateConfig
		self.ObjmultusdTools = ObjmultusdTools

		self.KeepThreadRunning = True
		self.multusdPingInterval = 5.0
		self.ObjPeriodic = None
		return

	############################################################
	def __del__(self):
		print ("leaving multusdClientTemplateOperateClass")
		pass

	############################################################
	def SetupPeriodicmessages(self, bPeriodicmultusdSocketPingEnable):
		bSuccess = False

		MaxSleepingTime = 1.0
		SleepingTime = MaxSleepingTime
		
		try:
			## We do the peridic stuff 5 times per period, so we get it right when checking it
			self.multusdPingInterval = self.ObjmultusdClientTemplateConfig.ModuleControlMaxAge / 5.0

			## setup the periodic alive mnessage stuff
			if bPeriodicmultusdSocketPingEnable:
				self.ObjmultusdTools.logger.debug("Setup the periodic Alive messages")
				self.TimestampNextmultusdPing = time.time()
				self.ObjPeriodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', self.ObjmultusdClientTemplateConfig.ModuleControlPort)
				if not self.ObjPeriodic.ConnectFeedbackSocket():
					self.ObjmultusdTools.logger.debug("Stopping Process, cannot establish Feedback Connection to multusd")
					sys.exit(1)

			# 2021-01-31 
			# do the touch thing to check alive status even if no control socket is activated
			if self.ObjmultusdClientTemplateConfig.ModuleControlFileEnabled:
				## maybe we do the checking only by timstamp of PID file and not by control port
				if not self.ObjPeriodic:
																										# dummy parameters
					self.ObjPeriodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', 888)
				
				## initialize the timspamp based stuff
																				## We do it twice as often as required, to ease the checking
				self.ObjPeriodic.InitCheckByThouch(self.ObjmultusdClientTemplateConfig.LPIDFile, (self.ObjmultusdClientTemplateConfig.ModuleControlMaxAge / 5.0))
				## We do the first check right here.. might be better after a shutdown by 9
				self.ObjPeriodic.DoCheckByTouch(time.time())

			# 2020-01-01
			# the loop shall not sleep longer than 1 second.. otherwise the handling in the stop procedure gets too slow
			SleepingTime = self.multusdPingInterval
			if self.multusdPingInterval > MaxSleepingTime:
				SleepingTime = MaxSleepingTime

			bSuccess = True

		except:
			ErrorString = self.ObjmultusdTools.FormatException()	
			self.ObjmultusdTools.logger.debug("SetupPeriodicmessages Fatal error setting up perodic stuff: " + ErrorString)

		return SleepingTime, bSuccess 

	############################################################
	def DoPeriodicMessage(self, bPeriodicmultusdSocketPingEnable):
		bSuccess = True
		Timestamp = time.time()

		## first we do the control port stuff and talk to the multud
		if bPeriodicmultusdSocketPingEnable and self.ObjPeriodic:
			if Timestamp >= self.TimestampNextmultusdPing:
				self.ObjPeriodic.SendPeriodicMessage()
				self.TimestampNextmultusdPing = time.time() + self.multusdPingInterval
				
			if self.ObjPeriodic.WeAreOnError:
				self.ObjmultusdTools.logger.debug("Error connecting to multusd... we stop running")
				bSuccess = false

		# 2021-01-31
		# Addition do the PID file touch stuff as well
		# the multusd checks the timestamp of the PID file.. it should not be too old..
		if self.ObjPeriodic:
			self.ObjPeriodic.DoCheckByTouch(Timestamp)

		return bSuccess 

	############################################################
	###
	### main funtion running the mein loop
	###
	def Operate(self, bPeriodicmultusdSocketPingEnable):

		## setup the periodic control stuff..
		## if this does not succeed .. we do not have to continue
		SleepingTime, self.KeepThreadRunning = self.SetupPeriodicmessages(bPeriodicmultusdSocketPingEnable)

		# here comes the endless loop
		while self.KeepThreadRunning:
			
			## We do the periodic messages and stuff to indicate that we are alive for the multusd
			self.KeepThreadRunning = self.DoPeriodicMessage(bPeriodicmultusdSocketPingEnable)
			
			## TODO
			## place your code for individual actions here
			##


			## End
			if self.KeepThreadRunning:
				time.sleep (SleepingTime)

		return
