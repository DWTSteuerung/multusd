# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2019-11-02
#
# the multusd config data... NOT the modules, but the multusd service
#
#

import os
import configparser

import DWTThriftConfig3

class ConfigDataClass(DWTThriftConfig3.ConfigDataClass):

	def __init__(self):
		DWTThriftConfig3.ConfigDataClass.__init__(self)
		self.SoftwareVersion = "20"

		self.LogFile = ""
		self.LoggingDir = ""
		self.PIDFilePath = ""
		self.PIDFile = ""
		self.multusUsersConfigFile = ""
		self.multusUsersClass = ""
		self.multusModulesConfigFile = ""
		self.multusModulesClass = ""
		self.ProcessorTemperatureEnabled = True
		self.ProcessorMinTemperature = 80.0
		self.ProcessorMaxTemperature = 80.0
		self.ProcessorTemperatureFile = ""
		self.ProcessorCoolDownHysteresis = 5.0

		### the only hard coded Init file name...
		self.multusdInitFile = "/multus/etc/multusd.conf"
		
		## 2020-01-22
		## because of the HWClass usage
		self.MySQLEnable = False
		self.MySQLThriftLoggingEnable = False

		## 2020-01-25
		self.GeneralHWWatchdogIsEnabled = False

		return

	def readConfig(self):
		config = configparser.ConfigParser()
		config.read(self.multusdInitFile, encoding='utf-8')

		print("multusd Opening InitFile: " + self.multusdInitFile)

		self.LoggingDir = config.get('DEFAULT', 'LoggingDir')

		# check the existance of the logging directory
		if not os.path.exists(self.LoggingDir):
			os.mkdir(self.LoggingDir)

		LogFile = config.get('DEFAULT', 'LogFile')
		self.LogFile = self.LoggingDir + "/" + LogFile

		self.PIDFilePath = config.get('DEFAULT', 'PIDFilePath')
		if not os.path.exists(self.PIDFilePath):
			os.mkdir(self.PIDFilePath)

		self.PIDFile = self.PIDFilePath + "/" + config.get('DEFAULT', 'PIDFile')
		
		StrWHWatchdogEnable = config.get('DEFAULT', 'GeneralHWWatchdogIsEnabled')

		if StrWHWatchdogEnable.lower() == "true" or StrWHWatchdogEnable == "1":
			self.GeneralHWWatchdogIsEnabled = True

		self.multusUsersConfigFile = config.get('BasicClasses', 'multusUsersConfigFile')
		self.multusUsersClass = config.get('BasicClasses', 'multusUsersClass')
		self.multusModulesConfigFile = config.get('BasicClasses', 'multusModulesConfigFile')
		self.multusModulesClass = config.get('BasicClasses', 'multusModulesClass')
		BoolStrValue = config.get('Prerequisites', 'ProcessorTemperatureEnabled')
		if BoolStrValue.lower() == "false" or BoolStrValue == "0":
			self.ProcessorTemperatureEnabled = False
		self.ProcessorMinTemperature = float(config.get('Prerequisites', 'ProcessorMinTemperature'))
		self.ProcessorMaxTemperature = float(config.get('Prerequisites', 'ProcessorMaxTemperature'))
		self.ProcessorTemperatureFile = config.get('Prerequisites', 'ProcessorTemperatureFile')
		self.ProcessorCoolDownHysteresis = float(config.get('Prerequisites', 'ProcessorCoolDownHysteresis'))

		return
