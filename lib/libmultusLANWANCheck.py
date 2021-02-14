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
import libmultusdClientBasisStuff
import multusdBasicConfigfileStuff
#import libDSVIntegrityStatus
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
	def __init__(self, Tools, ModuleConfig, Ident, DSVIntegrityEnabled):
		
		self.Ident = Ident

				## We get the gRPC stuff for doing refresh on DSVIntegrity, if enabled
		self.ObjDSVIntegrityStatus = None
		"""
		if DSVIntegrityEnabled:
			self.ObjDSVIntegrityStatus = libDSVIntegrityStatus.gRPCDSVIntegrityStatusClass(Tools)
			self.ObjDSVIntegrityStatus.gRPCSetupDSVIntegrityConnection()
		"""
		
		self.RefreshPeriodicInterval = 10.0
		self.NextRefreshPeriodic = time.time() + self.RefreshPeriodicInterval
		
		return

	def SetIntoFailSafeState(self, ProcessIsRunning):
		if self.ObjDSVIntegrityStatus:
			self.ObjDSVIntegrityStatus.gRPCSendProcessStatusmultusd(self.Ident, False, bForce = True)
		return

	def ExecuteAfterStop(self, ProcessIsRunning):
		if self.ObjDSVIntegrityStatus:
			self.ObjDSVIntegrityStatus.gRPCSendProcessStatusmultusd(self.Ident, False, bForce = True)

		return

	def ExecuteAfterStart(self, ProcessIsRunning):
		if self.ObjDSVIntegrityStatus:
			self.ObjDSVIntegrityStatus.gRPCSendProcessStatusmultusd(self.Ident, ProcessIsRunning, bForce = True)

		return

	def ExecutePeriodic(self, ProcessIsRunning):
		if self.ObjDSVIntegrityStatus:
			Timestamp = time.time()
			if Timestamp >= self.NextRefreshPeriodic:
				self.ObjDSVIntegrityStatus.gRPCSendProcessStatusmultusd(self.Ident, ProcessIsRunning, bForce = False)
				self.NextRefreshPeriodic = time.time() + self.RefreshPeriodicInterval

		return
############################################################################################################

class multusLANWANCheckConfigClass(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):
	def __init__(self, ConfigFile):
		## initialize the parent class
		multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		self.ConfigFile = ConfigFile

		# 2021-02-07
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


class gRPCOperateClass(libmultusdClientBasisStuff.multusdClientBasisStuffClass):
	def __init__(self, ObjmultusLANWANCheckConfig, ObjmultusdTools):
		# init parent class
		libmultusdClientBasisStuff.multusdClientBasisStuffClass.__init__(self, ObjmultusLANWANCheckConfig, ObjmultusdTools)

		self.ObjmultusLANWANCheckConfig = ObjmultusLANWANCheckConfig
		
		self.LANCheckInterval = 10.0

		self.ObjConnectionChecks = ConnectionCheckClass(ObjmultusLANWANCheckConfig, ObjmultusdTools)

		return

	def __del__(self):
		self.ObjDSVIntegrityStatus.gRPCSendProcessStatusClient(self.ObjmultusLANWANCheckConfig.Ident, False, bForce = True)
		return

	############################################################
	###
	### main funtion running the main loop
	###
	#def RungRPCServer(self, multusdPingInterval, periodic):
	def RungRPCServer(self, bPeriodicmultusdSocketPingEnable):
		## setup the periodic control stuff..
		## if this does not succeed .. we do not have to continue
		SleepingTime, self.KeepThreadRunning = self.SetupPeriodicmessages(bPeriodicmultusdSocketPingEnable)

		# 2021-02-14
		## We wat a time tille we check everything for the first time
		## everything has to settle after starting
		StartupDelay = 60.0
		TimestampNextLANCheck = time.time() + StartupDelay
		TimestampNextWANCheck = time.time() + StartupDelay
		
		# declare a server object with desired number
		# of thread pool workers.
		self.gRPCServer = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
 
		# This line can be ignored
		LANWANOVPNCheck_pb2_grpc.add_gRPCServiceServicer_to_server(gRPCServiceServicer(self.ObjmultusdTools, self.ObjConnectionChecks),self.gRPCServer)
 
		# bind the server to the port defined above
		self.gRPCServer.add_insecure_port('[::]:{}'.format(self.ObjmultusLANWANCheckConfig.WANCheckResultPort))
 
		# start the server
		self.gRPCServer.start()
		self.ObjmultusdTools.logger.debug('gRPCService Server running ...')

		OldProcessHealthStatus = self.ObjConnectionChecks.ProcessHealthStatus
		self.ObjDSVIntegrityStatus = None
		print ("multusDSVIntegrity Enabled: " + str(self.ObjmultusLANWANCheckConfig.DSVIntegrityEnabled))
		if self.ObjmultusLANWANCheckConfig.DSVIntegrityEnabled:
			self.ObjDSVIntegrityStatus = libDSVIntegrityStatus.gRPCDSVIntegrityStatusClass(self.ObjmultusdTools)
			self.ObjDSVIntegrityStatus.gRPCSetupDSVIntegrityConnection()

		while self.KeepThreadRunning:
			bRunJustATest = False
			## We do the periodic messages and stuff to indicate that we are alive for the multusd
			self.KeepThreadRunning = self.DoPeriodicMessage(bPeriodicmultusdSocketPingEnable)

			Timestamp = time.time()
			if self.ObjmultusLANWANCheckConfig.LANCheckEnable and Timestamp >= TimestampNextLANCheck: 
				self.ObjConnectionChecks.runLANCheck()
				TimestampNextLANCheck = Timestamp + self.LANCheckInterval
				bRunJustATest = True

			## We check the WAN connection only, in case we did not have checked the LAN within the same run
			## And we check it only, if LAN Check is enabled
			if not bRunJustATest and self.ObjmultusLANWANCheckConfig.LANCheckEnable and self.ObjmultusLANWANCheckConfig.WANCheckEnable and Timestamp >= TimestampNextWANCheck:
				self.ObjConnectionChecks.runWANCheck(self.ObjmultusLANWANCheckConfig.WANCheckAdresses)
				TimestampNextWANCheck = Timestamp + self.ObjmultusLANWANCheckConfig.WANCheckInterval
				bRunJustATest = True

			## the most important assignment, which is evaluated by DSVIntegrity
			self.ObjConnectionChecks.ProcessHealthStatus = (self.ObjConnectionChecks.LANConnectionStatus.ConnectionStatus or not self.ObjmultusLANWANCheckConfig.LANCheckEnable) \
			and (self.ObjConnectionChecks.WANConnectionStatus.ConnectionStatus or not (self.ObjmultusLANWANCheckConfig.LANCheckEnable and self.ObjmultusLANWANCheckConfig.WANCheckEnable))

			if self.ObjmultusLANWANCheckConfig.DSVIntegrityEnabled and OldProcessHealthStatus != self.ObjConnectionChecks.ProcessHealthStatus:
				self.ObjDSVIntegrityStatus.gRPCSendProcessStatusClient(self.ObjmultusLANWANCheckConfig.Ident, self.ObjConnectionChecks.ProcessHealthStatus, bForce = True)
				OldProcessHealthStatus = self.ObjConnectionChecks.ProcessHealthStatus
			elif self.ObjmultusLANWANCheckConfig.DSVIntegrityEnabled:
				self.ObjDSVIntegrityStatus.gRPCSendProcessStatusClient(self.ObjmultusLANWANCheckConfig.Ident, self.ObjConnectionChecks.ProcessHealthStatus, bForce = False)

			if self.KeepThreadRunning and not bRunJustATest:
				time.sleep (SleepingTime)

		self.ObjmultusdTools.logger.debug('gRPCService Server Stopped ...')

