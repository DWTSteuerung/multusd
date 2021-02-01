# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2019-12-08
#
# After changing the FailSafe technology 
#
# 2020-10-27
# made it work in reality
#
import os
import sys
import time
import configparser
import subprocess

sys.path.append('/multus/lib')
## do the Periodic Alive Stuff
import multusdControlSocketClient
import multusdBasicConfigfileStuff

# 2020-06-01
# Json config option
UseJsonConfig = False
import urllib.request

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

class multusLANConfigClass(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):
	def __init__(self, ConfigFile):
		## initialize the parent class
		multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		self.ConfigFile = ConfigFile
		self.SoftwareVersion = "1"
	
		self.ReloadNetworkDirectory = None

		self.ModuleControlFileEnabled = False
		return

	def ReadConfig(self):
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden == True:
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')

			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))
			self.NoWANEnable = self.__assignBool__(config.get('NoWANEnable', 'Value'))
			self.WANviaLANEnable = self.__assignBool__(config.get('WANviaLANEnable', 'Value'))

			self.DHCPClientEnable = self.__assignBool__(config.get('DHCPClientEnable', 'Value'))

			self.LANIP = self.__assignStr__(config.get('LANIP', 'Value'))
			self.LANNetMask = self.__assignStr__(config.get('LANNetMask', 'Value'))
			self.Gateway = self.__assignStr__(config.get('Gateway', 'Value'))
			self.Nameserver = self.__assignStr__(config.get('Nameserver', 'Value'))

			self.SourceNatEnable = self.__assignBool__(config.get('SourceNatEnable', 'Value'))
			self.DestNatEnable = self.__assignBool__(config.get('DestNatEnable', 'Value'))
			self.DNatNetwork = self.__assignStr__(config.get('DNatNetwork', 'Value'))
			self.DNatNetMask = self.__assignStr__(config.get('DNatNetMask', 'Value'))

			self.LANInterface = self.__assignStr__(config.get('LANInterface', 'Value'))
			self.DHCPCDTemplate = self.__assignStr__(config.get('DHCPCDTemplate', 'Value'))
			self.DHCPCDDestination = self.__assignStr__(config.get('DHCPCDDestination', 'Value'))
			self.RestartNetworkingCommand = self.__assignStr__(config.get('RestartNetworkingCommand', 'Value'))
		else:

			print ("No config file .. exiting")
			return False

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
							break

						InstanceCounter += 1

			bSuccess = True
		except:
			ErrorString = ObjmultusdTools.FormatException()
			LogString = "Read in Json Process config failed with Error: " + ErrorString
			print(LogString)
			
		return bSuccess

############################################################################################################

class multusLANOperateClass(object):
	def __init__(self, ObjmultusLANConfig, ObjmultusdTools):

		self.ObjmultusLANConfig = ObjmultusLANConfig
		self.ObjmultusdTools = ObjmultusdTools

		self.KeepThreadRunning = True
		
		return

	def __del__(self):
		print ("leaving multusLANOperateClass")
		pass

	def CheckReloadNetwork(self, WeDoItCounter):
		DoSleep = True
		if not os.path.isfile(self.ObjmultusLANConfig.ReloadProcess):
			WeDoItCounter -= 1
			if (WeDoItCounter == 0):
				if (os.path.isfile(self.ObjmultusLANConfig.ReloadNetworkFile) and os.path.isfile(self.ObjmultusLANConfig.DHCPCDTemplate)):	
					self.ObjmultusdTools.logger.debug("Reload of network configuration requested - DHCPEnable: " + str(self.ObjmultusLANConfig.DHCPClientEnable))
					DoSleep = False

					## write /etc/dhcpcd.conf
					FileW = open(self.ObjmultusLANConfig.DHCPCDDestination, 'w')

					## read in template
					with open(self.ObjmultusLANConfig.DHCPCDTemplate, 'r') as FileR:
						# Read & write the entire file
						FileW.write(FileR.read())

					#Now we depen on DHCP or not
					if not self.ObjmultusLANConfig.DHCPClientEnable:
						FileW.write("\n#\n#Autogenerated by multusLAN.py\n#\n\n")
						FileW.write("interface " + self.ObjmultusLANConfig.LANInterface + "\n")
						#FileW.write("arping " + self.ObjmultusLANConfig.Gateway + "\n\n")
						#FileW.write("profile " + self.ObjmultusLANConfig.Gateway + "\n")
						FileW.write("static ip_address=" + self.ObjmultusLANConfig.LANIP + self.ObjmultusLANConfig.LANNetMask + "\n")
						FileW.write("static routers=" + self.ObjmultusLANConfig.Gateway + "\n")
						FileW.write("static domain_name_servers=" + self.ObjmultusLANConfig.Nameserver + "\n\n")

					self.ObjmultusdTools.logger.debug("Wrote out Config File: " + self.ObjmultusLANConfig.DHCPCDDestination)
					FileW.close()

					## /bin/systemctl restart network -- reload?
					subprocess.call([self.ObjmultusLANConfig.RestartNetworkingCommand])
					self.ObjmultusdTools.logger.debug("Restarted Network by executing: " + self.ObjmultusLANConfig.RestartNetworkingCommand)

					os.remove(self.ObjmultusLANConfig.ReloadNetworkFile)
					WeDoItCounter = 30
				else:
					WeDoItCounter = 30

		return DoSleep, WeDoItCounter 

	def Operate(self, multusdPingInterval, bPeriodicEnable, ModuleControlPort):

		## setup the perodic alive mnessage stuff
		ObjPerodic = None
		if bPeriodicEnable:
			print ("Setup the perodic Alive messages")
			TimestampNextmultusdPing = time.time()
			ObjPerodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', ModuleControlPort)
			if not ObjPerodic.ConnectFeedbackSocket():
				self.ObjmultusdTools.logger.debug("Stopping Process, cannot establish Feedback Connection to multusd")
				sys.exit(1)

		#ObjPerodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', ModuleControlPort)
		#TimestampNextmultusdPing = time.time() + 100000.0
			
		# 2021-01-31 
		# do the touch thing to check alive status 
		if self.ObjmultusLANConfig.ModuleControlFileEnabled:
			if not ObjPerodic:
				ObjPerodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', 888)

																			## We do it twice as often as required, to ease the checking
			ObjPerodic.InitCheckByThouch(self.ObjmultusLANConfig.LPIDFile, (self.ObjmultusLANConfig.ModuleControlMaxAge / 2.0))


		# 2020-01-01
		# the loop shall not sleep longer than 1 second.. otherwise the handling in the stop procedure gets too slow
		SleepingTime = multusdPingInterval
		if multusdPingInterval > 1.0:
			SleepingTime = 1.0

		DoSleep = True
		WeDoItCounter = 30

		NotToDoCounter = 0
		while self.KeepThreadRunning:
			Timestamp = time.time()
			if bPeriodicEnable and ObjPerodic and Timestamp >= TimestampNextmultusdPing:
				ObjPerodic.SendPeriodicMessage()
				TimestampNextmultusdPing = time.time() + multusdPingInterval
								
				if ObjPerodic.WeAreOnError:
					self.ObjmultusdTools.logger.debug("Error connecting to multusd... we stop running")
					self.KeepThreadRunning = False
				
			# 2021-01-31
			# Addition do the PID file touch stuff as well
			if ObjPerodic and NotToDoCounter < 10:
				ObjPerodic.DoCheckByTouch(Timestamp)
				#NotToDoCounter += 1

			## first we check on any changes
			DoSleep, WeDoItCounter = self.CheckReloadNetwork(WeDoItCounter)


			if DoSleep and self.KeepThreadRunning:
				time.sleep (SleepingTime)

		return
