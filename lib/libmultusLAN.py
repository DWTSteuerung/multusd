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
import multusdBasicConfigfileStuff
import libmultusdClientBasisStuff

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

class multusLANOperateClass(libmultusdClientBasisStuff.multusdClientBasisStuffClass):
	def __init__(self, ObjmultusLANConfig, ObjmultusdTools):
		# init parent class
		libmultusdClientBasisStuff.multusdClientBasisStuffClass.__init__(self, ObjmultusLANConfig, ObjmultusdTools)

		self.ObjmultusLANConfig = ObjmultusLANConfig
		
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

	def Operate(self, bPeriodicmultusdSocketPingEnable):
	
		## setup the periodic control stuff..
		## if this does not succeed .. we do not have to continue
		SleepingTime, self.KeepThreadRunning = self.SetupPeriodicmessages(bPeriodicmultusdSocketPingEnable)

		DoSleep = True
		WeDoItCounter = 30

		NotToDoCounter = 0
		while self.KeepThreadRunning:
				
			## We do the periodic messages and stuff to indicate that we are alive for the multusd
			self.KeepThreadRunning = self.DoPeriodicMessage(bPeriodicmultusdSocketPingEnable)

			### TODO 
			### Extremely complicated an not reliable
			#
			## first we check on any changes
			DoSleep, WeDoItCounter = self.CheckReloadNetwork(WeDoItCounter)

			if DoSleep and self.KeepThreadRunning:
				time.sleep (SleepingTime)

		return
