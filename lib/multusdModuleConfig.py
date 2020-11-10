# -*- coding: utf-8 -*-
# Karl Keusgen
# 2019-10-30
#
# Read in /usr/local/etc/multus/php/BasicInfos.conf
# Get the multusModulesConfig Paremeter
#
# Read in the Modules config..
# get the enabled modules and their startup routines

import configparser
import pprint
import inspect 
import sys
import os

sys.path.append('/multus/lib')
import multusdBasicConfigfileStuff

class ClassModuleConfig(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):
	class ClassModulesHandling(object):
		class ClassModules(object):
			def __init__(self):
				self.ModuleIdentifier = ""
				self.BasicIdentifier = ""
				self.RunOnce = True	
				## this is a generated value
				self.ModulePIDFile = ""

				self.ModuleDescription = ""
				self.ModulePHPHeadline = ""
				self.ModuleClass = ""
				self.ModuleConfig = ""
				self.EditRightLevel = list()
				self.Enabled = False
				self.ModulePosition = 100
				self.PHPPage = ""
				self.ModuleIsAService = True

				self.ModuleBinaryStartupDirectlyEnable = False
				self.ModuleBinaryPath = ""
				self.ModuleBinary = ""
				self.ModuleBinaryParameter = ""
				self.ModuleControlPort = 0
				self.ModuleControlPortEnabled = False
				self.ModuleControlFileEnabled = False
				self.ModuleControlMaxAge = 0.0
				self.MaxTimeWaitForShutdown = 2.0

				self.ModuleServiceUser = "admin"
				self.ModuleStartScript = ""
				self.ModuleStartScriptParameter = ""
				self.ModuleStopScript = ""
				self.ModuleStopScriptParameter = ""
				self.ModuleStatusByPIDFileEnable = False
				self.ModuleStatusByPIDFilePeriod = 5
				self.ModuleStatusScript = ""
				self.ModuleStatusScriptParameter = ""
				self.ModuleCheckScript = ""
				self.ModulePeriodicCheckInterval = 300
				self.ModulePeriodicCheckEnabled = False

		def __init__(self):
			self.ModuleParameter = self.ClassModules()
			self.ThreadLastTimeStarted = 0.0
			self.ControlThreadLastTimeStarted = 0.0
			self.ProcessLastTimeStarted = 0.0
			self.ControlThread = None # variable to keep the pointer on the THread running the listening Control Port
			self.ControlThreadErrorLoggingDone = False
			self.Thread = None # variable to keep the pointer on the thread instance lateron, the thread starting and stopping the process
			self.ThreadErrorLoggingDone = False

			# 2019-12-04
			self.dBNKEnabled = False

	def __init__(self, multusdConfig):
		print ("starting ClassModuleConfig")

		# don't know whether i need them or not.. but now they are there
		self.multusdConfig = multusdConfig
		
		## initialize the parent class
		multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		## Array, in which the modules will be strored lateron generate
		self.AllModules = list();
		self.EnabledServicesModules = list();
		
		return

	def ReadModulesConfig(self):
		# first empty the old lists.. if there are one
		PythonVersion = sys.version
		#print ("Now there comes the version of the python interpreter.. hopefully")
		#print (PythonVersion[0])
		
		if float(PythonVersion[0]) >= 3:
			#print ("We are running not Python 2.7 and clearing the lists now")
			self.AllModules.clear()
			self.EnabledServicesModules.clear()

		self.__ReadModules__(self.multusdConfig.multusModulesConfigFile)

		return
	############################################################################################################
	def __del__(self):
		print ("exiting ClassModuleConfig")
	
		return

	############################################################################################################
	def __ReadModules__(self, ConfigFile):
		
		print ("Read in the Modules from ConfigFile: " + ConfigFile)

		ModuleConfig =  configparser.ConfigParser()
		ModuleConfig.read(ConfigFile)

		for Element in ModuleConfig:
			#print (Element)
			
			if Element != "DEFAULT":

				## 2019-12-30
				## We can run some modules in more than 1 instances.. we check this first
				RunOnce = True
				RunInstances = 1
				Instance = 0
				try:
					RunOnce = self.__assignBool__(ModuleConfig[Element]['RunOnce'])
					RunInstances = self.__assignInt__(ModuleConfig[Element]['RunInstances'])
				except:
					pass

				#print ("Modul " + str(Element) + " RunOnce Parameter: " + str(RunOnce) + " RunInstances Parameter: " + str(RunInstances))

				while Instance < RunInstances:
					#print ("Modul " + str(Element) + " Create Instance: " + str(Instance))
					self.AllModules.append(self.ClassModulesHandling())

					#for SubElement in ModuleConfig[Element]:
					#	print (SubElement)
					self.AllModules[-1].ModuleParameter.RunOnce = RunOnce

					## Set values of the last, just appended element
					self.AllModules[-1].ModuleParameter.ModuleIdentifier = self.__assignStr__(ModuleConfig[Element]['ModuleIdentifier'])
					self.AllModules[-1].ModuleParameter.BasicIdentifier = self.__assignStr__(ModuleConfig[Element]['ModuleIdentifier'])

					if not RunOnce:
						self.AllModules[-1].ModuleParameter.ModuleIdentifier = self.AllModules[-1].ModuleParameter.ModuleIdentifier + "_" + str(Instance)
					else:
						## to make sure, the this loop runs only once, no matter how the RunInstances parameter is configured
						RunInstances = 1

					self.AllModules[-1].ModuleParameter.ModulePIDFile = self.multusdConfig.PIDFilePath + "/" + self.AllModules[-1].ModuleParameter.ModuleIdentifier + ".pid"
					self.AllModules[-1].ModuleParameter.ModuleDescription = self.__assignStr__(ModuleConfig[Element]['ModuleDescription'])
					self.AllModules[-1].ModuleParameter.ModulePHPHeadline = self.__assignNone__(ModuleConfig[Element]['ModulePHPHeadline'])
					self.AllModules[-1].ModuleParameter.ModuleClass = self.__assignNone__(ModuleConfig[Element]['ModuleClass'])
					self.AllModules[-1].ModuleParameter.ModuleConfig = self.__assignNone__(ModuleConfig[Element]['ModuleConfig'])
					if not RunOnce:
						ConfigArray = self.AllModules[-1].ModuleParameter.ModuleConfig.split('.')
						
						self.AllModules[-1].ModuleParameter.ModuleConfig = ConfigArray[0] + "_" + str(Instance) + "." + ConfigArray[1]
						#print ("We build ConfigFile: " + self.AllModules[-1].ModuleParameter.ModuleConfig)
					## Now there comnes an php array in the config file.. we try to handle this
					i = 0
					bBreak = False
					while not bBreak:
						try:
							self.__assignIntPHPArray__(self.AllModules[-1].ModuleParameter.EditRightLevel, ModuleConfig[Element]['EditRightLevel['+ str(i) +']'])
							
							i = i + 1
						except:
							#print ("Element " + str(i) + " does not exist.. we break loop")
							bBreak = True

					StupidValue = ModuleConfig[Element]['Enabled']
					#print ("very stupid enabled Value: " + str(StupidValue) + " Bullshit") 
					self.AllModules[-1].ModuleParameter.Enabled = self.__assignBool__(ModuleConfig[Element]['Enabled'])
					self.AllModules[-1].ModuleParameter.ModulePosition = self.__assignInt__(ModuleConfig[Element]['ModulePosition'])
					self.AllModules[-1].ModuleParameter.PHPPage = self.__assignNone__(ModuleConfig[Element]['PHPPage'])
					self.AllModules[-1].ModuleParameter.ModuleIsAService = self.__assignBool__(ModuleConfig[Element]['ModuleIsAService'])

					self.AllModules[-1].ModuleParameter.ModuleServiceUser = self.__assignNone__(ModuleConfig[Element]['ModuleServiceUser'])
					self.AllModules[-1].ModuleParameter.ModuleStartScript = self.__assignNone__(ModuleConfig[Element]['ModuleStartScript'])
					self.AllModules[-1].ModuleParameter.ModuleStartScriptParameter = self.__assignNone__(ModuleConfig[Element]['ModuleStartScriptParameter'])
					self.AllModules[-1].ModuleParameter.ModuleBinaryStartupDirectlyEnable = self.__assignBool__(ModuleConfig[Element]['ModuleBinaryStartupDirectlyEnable'])
					self.AllModules[-1].ModuleParameter.ModuleBinaryPath = self.__assignNone__(ModuleConfig[Element]['ModuleBinaryPath'])
					self.AllModules[-1].ModuleParameter.ModuleBinary = self.__assignNone__(ModuleConfig[Element]['ModuleBinary'])
					if not RunOnce and self.AllModules[-1].ModuleParameter.ModuleBinaryStartupDirectlyEnable:
						BinaryArray = self.AllModules[-1].ModuleParameter.ModuleBinary.split('.')
						
						self.AllModules[-1].ModuleParameter.ModuleBinary = BinaryArray[0] + "_" + str(Instance) + "." + BinaryArray[1]
						#print ("We build binary to run: " + self.AllModules[-1].ModuleParameter.ModuleBinary)

					self.AllModules[-1].ModuleParameter.ModuleBinaryParameter = self.__assignNone__(ModuleConfig[Element]['ModuleBinaryParameter'])
					self.AllModules[-1].ModuleParameter.ModuleControlPort = self.__assignInt__(ModuleConfig[Element]['ModuleControlPort'])
					#print ("Native ControlPort is: " + str(self.AllModules[-1].ModuleParameter.ModuleControlPort))
					if not RunOnce and self.AllModules[-1].ModuleParameter.ModuleBinaryStartupDirectlyEnable:
						self.AllModules[-1].ModuleParameter.ModuleControlPort = self.AllModules[-1].ModuleParameter.ModuleControlPort + Instance
						#print ("Instance " + str(Instance) + " ControlPort is: " + str(self.AllModules[-1].ModuleParameter.ModuleControlPort))

					self.AllModules[-1].ModuleParameter.ModuleControlPortEnabled = self.__assignBool__(ModuleConfig[Element]['ModuleControlPortEnabled'])
					self.AllModules[-1].ModuleParameter.ModuleControlFileEnabled = self.__assignBool__(ModuleConfig[Element]['ModuleControlFileEnabled'])
					self.AllModules[-1].ModuleParameter.ModuleControlMaxAge = self.__assignFloat__(ModuleConfig[Element]['ModuleControlMaxAge'])
					self.AllModules[-1].ModuleParameter.MaxTimeWaitForShutdown = self.__assignFloat__(ModuleConfig[Element]['MaxTimeWaitForShutdown'])
					self.AllModules[-1].ModuleParameter.ModuleStopScript = self.__assignNone__(ModuleConfig[Element]['ModuleStopScript'])
					self.AllModules[-1].ModuleParameter.ModuleStopScriptParameter = self.__assignNone__(ModuleConfig[Element]['ModuleStopScriptParameter'])
					self.AllModules[-1].ModuleParameter.ModuleCheckScript = self.__assignNone__(ModuleConfig[Element]['ModuleCheckScript'])
					self.AllModules[-1].ModuleParameter.ModuleStatusByPIDFileEnable = self.__assignBool__(ModuleConfig[Element]['ModuleStatusByPIDFileEnable'])
					self.AllModules[-1].ModuleParameter.ModuleStatusByPIDFilePeriod = self.__assignInt__(ModuleConfig[Element]['ModuleStatusByPIDFilePeriod'])
					self.AllModules[-1].ModuleParameter.ModuleStatusScript = self.__assignNone__(ModuleConfig[Element]['ModuleStatusScript'])
					self.AllModules[-1].ModuleParameter.ModuleStatusScriptParameter = self.__assignNone__(ModuleConfig[Element]['ModuleStatusScriptParameter'])
					self.AllModules[-1].ModuleParameter.ModulePeriodicCheckInterval = self.__assignInt__(ModuleConfig[Element]['ModulePeriodicCheckInterval'])
					self.AllModules[-1].ModuleParameter.ModulePeriodicCheckEnabled = self.__assignBool__(ModuleConfig[Element]['ModulePeriodicCheckEnabled'])

					#print ("Module " + Element + "/" + str(self.AllModules[-1].ModuleIdentifier) + " Enabled: " + str(self.AllModules[-1].Enabled) + " IsAService: " + str(self.AllModules[-1].ModuleIsAService))
					if self.AllModules[-1].ModuleParameter.Enabled and self.AllModules[-1].ModuleParameter.ModuleIsAService:
						print (Element + " Is an enabled service")
						self.EnabledServicesModules.append(self.AllModules[-1])

					#pprint.pprint (inspect.getmembers(self.AllModules[-1]))

					Instance = Instance + 1
				# End while
		return


####### test functionality
if __name__ == "__main__":

	Tester = ClassModuleConfig("/usr/local/etc/multus/php/BasicInfos.conf")
