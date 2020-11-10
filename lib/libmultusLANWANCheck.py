# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2019-11-24
# the firts gRPC protobuf based application of mine
#
# 2019-12-06
# put into a new structure
#
# 2019-12-31
# detached the LANWAN Check funtionality from the multusLAN process
#
import sys
import time
import subprocess
import os
import configparser

sys.path.append('/multus/lib')
import multusdBasicConfigfileStuff
"""
import libmultusdBNKStatus
"""
import libmultusLAN

## now the protobuf stuff
import grpc

sys.path.append('/multus/lib/proto')
import LANWANOVPNCheck_pb2
import LANWANOVPNCheck_pb2_grpc
from concurrent import futures

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

				## We get the gRPC stuff for doing refresh on dBNK, if enabled
		self.ObjdBNKStatus = None
		"""
		if dBNKEnabled:
			self.ObjdBNKStatus = libmultusdBNKStatus.gRPCdBNKStatusClass(Tools)
			self.ObjdBNKStatus.gRPCSetupdBNKConnection()
		"""
		
		self.RefreshPeriodicInterval = 10.0
		self.NextRefreshPeriodic = time.time() + self.RefreshPeriodicInterval
		
		return

	def SetIntoFailSafeState(self, ProcessIsRunning):
		if self.ObjdBNKStatus:
			self.ObjdBNKStatus.gRPCSendProcessStatusmultusd(self.Ident, False, bForce = True)
		return

	def ExecuteAfterStop(self, ProcessIsRunning):
		if self.ObjdBNKStatus:
			self.ObjdBNKStatus.gRPCSendProcessStatusmultusd(self.Ident, False, bForce = True)

		return

	def ExecuteAfterStart(self, ProcessIsRunning):
		if self.ObjdBNKStatus:
			self.ObjdBNKStatus.gRPCSendProcessStatusmultusd(self.Ident, ProcessIsRunning, bForce = True)

		return

	def ExecutePeriodic(self, ProcessIsRunning):
		if self.ObjdBNKStatus:
			Timestamp = time.time()
			if Timestamp >= self.NextRefreshPeriodic:
				self.ObjdBNKStatus.gRPCSendProcessStatusmultusd(self.Ident, ProcessIsRunning, bForce = False)
				self.NextRefreshPeriodic = time.time() + self.RefreshPeriodicInterval

		return
############################################################################################################

class multusLANWANCheckConfigClass(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):
	def __init__(self, ConfigFile):
		## initialize the parent class
		multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		self.ConfigFile = ConfigFile
		self.SoftwareVersion = "20"
		
		return

	def ReadConfig(self):
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden == True:
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')

			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))
			self.LANCheckEnable = self.__assignBool__(config.get('LANCheckEnable', 'Value'))
			self.LANCheckInterval = self.__assignInt__(config.get('LANCheckInterval', 'Value'))
			self.WANCheckEnable = self.__assignBool__(config.get('WANCheckEnable', 'Value'))
			self.WANCheckInterval = self.__assignInt__(config.get('WANCheckInterval', 'Value'))
			self.WANCheckAdresses =  self.__assignStrArray__(config.get('WANCheckAdresses', 'Value'))
			self.WANCheckResultPort = self.__assignInt__(config.get('WANCheckResultPort', 'Value'))

		else:

			print ("No config file .. exiting")
			return False

		print ("multusLANWANCheck started and read in its parameters")
		print ("WAN Check adresses: " + str(self.WANCheckAdresses))
		
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
							self.LANCheckEnable = bool(int(SingleInstance['LANCheckEnable']))
							self.LANCheckInterval = int(SingleInstance['LANCheckInterval'])
							self.WANCheckEnable = bool(int(SingleInstance['WANCheckEnable']))
							self.WANCheckInterval = int(SingleInstance['WANCheckInterval'])
							WANCheckAdresses = SingleInstance['WANCheckAdresses']
							self.WANCheckAdresses = WANCheckAdresses.split(',')
							self.WANCheckResultPort = int(SingleInstance['WANCheckResultPort'])

							break

						InstanceCounter += 1

			bSuccess = True
		except:
			ErrorString = ObjmultusdTools.FormatException()
			LogString = "Read in Json Process config failed with Error: " + ErrorString
			print(LogString)
			
		return bSuccess

	## 2019-12-31
	## We need to get the parameter NoWANEnable aout of the standard NetworkConfiguration
	## it is used in Network status lib NetworkStatus.py
	def ReadInmultusLANConfig(self, multusLANConfig):
		ObjmultusLANConfig = libmultusLAN.multusLANConfigClass(multusLANConfig)
		ObjmultusLANConfig.ReadConfig()
		self.NoWANEnable = ObjmultusLANConfig.NoWANEnable
		return

class ConnectionStatusClass(object):
	def __init__(self):
		self.TimestampLastCheck = None
		self.TimestampLastOK = None
		self.ConnectionStatus = None

class ConnectionCheckClass(object):
	def __init__(self, ObjmultusLANWANCheckConfig, ObjmultusdTools):

		## The health status of this process is ok, if LAN and WAN is working.. 
		self.ProcessHealthStatus = False

		self.ObjmultusLANWANCheckConfig = ObjmultusLANWANCheckConfig
		self.ObjmultusdTools = ObjmultusdTools

		self.LANConnectionStatus = ConnectionStatusClass()
		self.WANConnectionStatus = ConnectionStatusClass()

		return

	def runLANCheck(self):
		print ("Run LANCheck")
		self.LANConnectionStatus.TimestampLastCheck = time.time()
		self.LANConnectionStatus.TimestampLastOK = time.time()
		self.LANConnectionStatus.ConnectionStatus = True

		return

	def runWANCheck(self, WANCheckAdresses):
		print ("Run WANCheck")
		
		self.WANConnectionStatus.TimestampLastCheck = time.time()
		LocalStatus = False

		for ServerToCheck in WANCheckAdresses:
			print ("Now Checking against server: " + ServerToCheck)
			RV = subprocess.call(["/bin/ping", "-c 4",  ServerToCheck])
			if RV == 0:
				LocalStatus = True
				self.WANConnectionStatus.TimestampLastOK = time.time()

			break

		self.WANConnectionStatus.ConnectionStatus = LocalStatus
		return
 
class gRPCServiceServicer(LANWANOVPNCheck_pb2_grpc.gRPCServiceServicer):

	def __init__(self, ObjmultusdTools, ObjConnectionChecks):

		self.ObjmultusdTools = ObjmultusdTools
		
		self.LANcount = 0
		self.WANcount = 0

		self.TestTimestamp = 0.0

		self.ObjConnectionChecks = ObjConnectionChecks
		return

	def gRPCGetmultusLANWANCheckStatus(self, request, contect):
		result= {'ProcessOK': self.ObjConnectionChecks.ProcessHealthStatus}
		return LANWANOVPNCheck_pb2.ProcessStatusMessagemultusLANWANCheck(**result)

	def gRPCGetLANStatus(self, request, context):

		# get the string from the incoming request
		ReceivedString = request.RequestMessageMemberString
		print ("Received from Client: " + ReceivedString)

		LANStatus = self.ObjConnectionChecks.LANConnectionStatus

		self.LANcount = self.LANcount + 1
		result = {'TimestampLastCheck': LANStatus.TimestampLastCheck, 'TimestampLastOK': LANStatus.TimestampLastOK , 'ConnectionStatus': LANStatus.ConnectionStatus, 'count': self.LANcount, 'ValidStatus': True}
	
		print (str(result))
 
		return LANWANOVPNCheck_pb2.ResponseMessage(**result)

	def gRPCGetWANStatus(self, request, context):

		# get the string from the incoming request
		ReceivedString = request.RequestMessageMemberString
		print ("Received from Client: " + ReceivedString)
 	
		WANStatus = self.ObjConnectionChecks.WANConnectionStatus

		self.WANcount = self.WANcount + 1
 	
		result = {'TimestampLastCheck': WANStatus.TimestampLastCheck, 'TimestampLastOK': WANStatus.TimestampLastOK , 'ConnectionStatus': WANStatus.ConnectionStatus, 'count': self.WANcount, 'ValidStatus': True}
 
		return LANWANOVPNCheck_pb2.ResponseMessage(**result)

	#######################################################################################
	def gRPCgetLANWANCheckClientVersions(self, request, context):
		result = {'SoftwareVersion': self.ObjConnectionChecks.ObjmultusLANWANCheckConfig.SoftwareVersion, 'ConfigVersion': self.ObjConnectionChecks.ObjmultusLANWANCheckConfig.ConfigVersion}
		return LANWANOVPNCheck_pb2.LANWANOVPNCheckVersions(**result)


class gRPCOperateClass(object):
	def __init__(self, ObjmultusLANWANCheckConfig, ObjmultusdTools):

		self.ObjmultusLANWANCheckConfig = ObjmultusLANWANCheckConfig
		self.ObjmultusdTools = ObjmultusdTools

		self.KeepThreadRunning = True
		
		self.LANCheckInterval = 10.0

		self.ObjConnectionChecks = ConnectionCheckClass(ObjmultusLANWANCheckConfig, ObjmultusdTools)

		return

	def __del__(self):
		self.ObjdBNKStatus.gRPCSendProcessStatusClient(self.ObjmultusLANWANCheckConfig.Ident, False, bForce = True)
		return

	def RungRPCServer(self, multusdPingInterval, periodic):
		TimestampNextmultusdPing = time.time()

		TimestampNextLANCheck = time.time()
		TimestampNextWANCheck = time.time()
		
		# declare a server object with desired number
		# of thread pool workers.
		self.gRPCServer = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
 
		# This line can be ignored
		LANWANOVPNCheck_pb2_grpc.add_gRPCServiceServicer_to_server(gRPCServiceServicer(self.ObjmultusdTools, self.ObjConnectionChecks),self.gRPCServer)
 
		# bind the server to the port defined above
		self.gRPCServer.add_insecure_port('[::]:{}'.format(self.ObjmultusLANWANCheckConfig.WANCheckResultPort))
 
		# start the server
		self.gRPCServer.start()
		self.ObjmultusdTools.logger.debug('gRPCService Server running ...')

		OldProcessHealthStatus = self.ObjConnectionChecks.ProcessHealthStatus
		self.ObjdBNKStatus = None
		print ("multusdBNK Enabled: " + str(self.ObjmultusLANWANCheckConfig.dBNKEnabled))
		"""
		if self.ObjmultusLANWANCheckConfig.dBNKEnabled:
			self.ObjdBNKStatus = libmultusdBNKStatus.gRPCdBNKStatusClass(self.ObjmultusdTools)
			self.ObjdBNKStatus.gRPCSetupdBNKConnection()
		"""

		while self.KeepThreadRunning:
			# 2020-01-01
			# the loop shall not sleep longer than 1 second.. otherwise the handling in the stop procedure gets too slow
			SleepingTime = multusdPingInterval
			if multusdPingInterval > 1.0:
				SleepingTime = 1.0
			#self.ObjmultusdTools.logger.debug('gRPCService while loop, SleepingTime: ' + str(SleepingTime))

			Timestamp = time.time()
			if periodic and Timestamp >= TimestampNextmultusdPing:
				periodic.SendPeriodicMessage()
				TimestampNextmultusdPing = time.time() + multusdPingInterval
								
				if periodic.WeAreOnError:
					self.ObjmultusdTools.logger.debug("Error connecting to multusd... we stop running")
					self.KeepThreadRunning = False

			Timestamp = time.time()
			if Timestamp >= TimestampNextLANCheck: 
				self.ObjConnectionChecks.runLANCheck()
				TimestampNextLANCheck = Timestamp + self.LANCheckInterval
				SleepingTime = 0.0

			if self.ObjmultusLANWANCheckConfig.WANCheckEnable:
				Timestamp = time.time()
				if Timestamp >= TimestampNextWANCheck:
					self.ObjConnectionChecks.runWANCheck(self.ObjmultusLANWANCheckConfig.WANCheckAdresses)
					TimestampNextWANCheck = Timestamp + self.ObjmultusLANWANCheckConfig.WANCheckInterval
					SleepingTime = 0.0

			## the most important assignment, which is evaluated by dBNK
			self.ObjConnectionChecks.ProcessHealthStatus = self.ObjConnectionChecks.LANConnectionStatus.ConnectionStatus and self.ObjConnectionChecks.WANConnectionStatus.ConnectionStatus
			if self.ObjmultusLANWANCheckConfig.dBNKEnabled and OldProcessHealthStatus != self.ObjConnectionChecks.ProcessHealthStatus:
				self.ObjdBNKStatus.gRPCSendProcessStatusClient(self.ObjmultusLANWANCheckConfig.Ident, self.ObjConnectionChecks.ProcessHealthStatus, bForce = True)
				OldProcessHealthStatus = self.ObjConnectionChecks.ProcessHealthStatus
			elif self.ObjmultusLANWANCheckConfig.dBNKEnabled:
				self.ObjdBNKStatus.gRPCSendProcessStatusClient(self.ObjmultusLANWANCheckConfig.Ident, self.ObjConnectionChecks.ProcessHealthStatus, bForce = False)

			time.sleep (SleepingTime)

		self.ObjmultusdTools.logger.debug('gRPCService Server Stopped ...')

