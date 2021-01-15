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
import grpc
from concurrent import futures

sys.path.append('/multus/lib')
## do the Periodic Alive Stuff
import multusdControlSocketClient
#import multusdBasicConfigfileStuff
import DWTThriftConfig3
import multusHardwareHandler
import libmultusReadDIDOStatus

sys.path.append('/multus/lib/proto')
import multusReadDIDO_pb2
import multusReadDIDO_pb2_grpc

# 2020-06-01
# Json config option
import libUseJsonConfig
UseJsonConfig = libUseJsonConfig.UseJsonConfig
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
	def __init__(self, Tools, ModuleConfig, Ident, DSVIntegrityEnabled):
		
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

class multusReadDIDOConfigClass(DWTThriftConfig3.ConfigDataClass):
	class ClassHosts(object):
		def __init__(self, Hostname, Port):
			self.Hostname = Hostname
			self.Port = Port
			self.ObjgRPCmultusReadDIDOStatus = None

	def __init__(self, ConfigFile):
		## initialize the parent class
		DWTThriftConfig3.ConfigDataClass.__init__(self)
		#multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		self.ConfigFile = ConfigFile
		self.SoftwareVersion = "1"
		
		self.Instance = 0
	
		return

	def ReadConfig(self):
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden == True:
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')
			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))

			self.ReadInDIEnable = self.__assignBool__(config.get('ReadInDIEnable', 'Value'))

			self.ReadLastDOInsteadOfDI = self.__assignBool__(config.get('ReadLastDOInsteadOfDI', 'Value'))
			String = self.__assignStr__(config.get('RelevantDO', 'Value'))
			RelevantDO = String.split(',')
			self.RelevantDO = list()
			for DO in RelevantDO:
				self.RelevantDO.append(int(DO.strip()))

			self.TransferInterval = self.__assignInt__(config.get('TransferInterval', 'Value'))
			String = self.__assignStr__(config.get('DOHosts', 'Value'))
			DOHosts = String.split(',')
			self.DOHosts = list()
			for Host in DOHosts:
				DOHost = Host.split(':')
				self.DOHosts.append(self.ClassHosts(DOHost[0].strip(), int(DOHost[1].strip())))

			self.gRPCPort = self.__assignInt__(config.get('gRPCPort', 'Value'))
		
			self.MySQLEnable = self.__assignBool__(config.get('MySQLEnable', 'Value'))
			if self.MySQLEnable:
				### Wenn das True ist, dann koennen wir direkt die mysql Zugangs Parameter holen
				self.ThriftMysqlOpts = self.__ReadMySQLParameter__(self.ConfigFile)

				### Und wir schauen, ob wir in die Datenbank auch loggen sollen
				self.MySQLThriftLoggingEnable = self.__assignBool__(config.get('MySQLThriftLoggingEnable', 'Value'))

				self.MySQLRestoreDOEnable = self.__assignBool__(config.get('MySQLRestoreDOEnable', 'Value'))

		else:

			print ("No config file .. exiting")
			return False

		print ("multusReadDIDO started with these parameters")
		print ("multusReadDIDO : " + str(self.ConfigVersion))
		
		return True

	# 2020-06-01	
	def ReadJsonConfig(self, ObjmultusdTools, ObjmultusdJsonConfig, Ident, Instance = 0):
		self.Instance = Instance
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
class ClassmultusReadDIDOHandling(object):
	def __init__(self, ObjmultusReadDIDOConfig, ObjmultusdTools, ObjmultusHardware):

		self.ObjmultusdTools = ObjmultusdTools
		self.ObjmultusReadDIDOConfig = ObjmultusReadDIDOConfig
		self.ObjmultusHardware = ObjmultusHardware

		self.DIStatus = None
		self.DIStatusOld = None

		## setup the DOHosts
		for DOHost in self.ObjmultusReadDIDOConfig.DOHosts:
			DOHost.ObjgRPCmultusReadDIDOStatus = libmultusReadDIDOStatus.gRPCmultusReadDIDOStatusClass(self.ObjmultusdTools, DOHost.Hostname, DOHost.Port)

		self.gRPCRM = multusReadDIDO_pb2.MessageDigitalStatus(DI01 = -1, DI02 = -1, DI03 = -1, DI04 = -1, DI05 = -1, DI06 = -1, DI07 = -1, DI08 = -1)

		self.ProcessHealthStatus = True

		self.DOSet = self.ObjmultusHardware.InitDOSet()
		pass

	def TransferStatusToRemote(self, DIStatus):

		# prepare RequestMessage
		for RDO in self.ObjmultusReadDIDOConfig.RelevantDO:
			if RDO == 1:
				self.gRPCRM.DI01 = DIStatus[RDO - 1]

			elif RDO == 2:
				self.gRPCRM.DI02 = DIStatus[RDO - 1]

			elif RDO == 3:
				self.gRPCRM.DI03 = DIStatus[RDO - 1]

			elif RDO == 4:
				self.gRPCRM.DI04 = DIStatus[RDO - 1]

			elif RDO == 5:
				self.gRPCRM.DI05 = DIStatus[RDO - 1]

			elif RDO == 6:
				self.gRPCRM.DI06 = DIStatus[RDO - 1]

			elif RDO == 7:
				self.gRPCRM.DI07 = DIStatus[RDO - 1]

			elif RDO == 8:
				self.gRPCRM.DI08 = self.DIStatus[RDO - 1]


		for DOHost in self.ObjmultusReadDIDOConfig.DOHosts:
			self.ObjmultusdTools.logger.debug ("Distribute gRPC update -- " + str(self.gRPCRM.DI01) + ", " + str(self.gRPCRM.DI02) + ", " + str(self.gRPCRM.DI03) + ", " + str(self.gRPCRM.DI04) + ", " + str(self.gRPCRM.DI05) + ", " + str(self.gRPCRM.DI06) + ", " + str(self.gRPCRM.DI07) + ", " + str(self.gRPCRM.DI08) + " -- to Host: " + str(DOHost.Hostname))

			DOHost.ObjgRPCmultusReadDIDOStatus.SetDigitalOutputs(self.gRPCRM)

		return

	def __del__(self):
		pass


############################################################################################################
class gRPCmultusReadDIDOServicerClass(multusReadDIDO_pb2_grpc.gRPCmultusReadDIDOServicer):

	def __init__(self, ObjmultusReadDIDOHandling):

		self.ObjmultusReadDIDOHandling = ObjmultusReadDIDOHandling
		self.ObjmultusdTools = self.ObjmultusReadDIDOHandling.ObjmultusdTools
		self.ObjmultusReadDIDOConfig = self.ObjmultusReadDIDOHandling.ObjmultusReadDIDOConfig

		return

	def gRPCGetmultusReadDIDOStatus(self, request, contect):
		result= {'ProcessOK': self.ObjmultusReadDIDOHandling.ProcessHealthStatus}
		return multusReadDIDO_pb2.ProcessStatusMessagemultusReadDIDO(**result)

	#######################################################################################
	def gRPCgetmultusReadDIDOVersions(self, request, context):
		result = {'SoftwareVersion': self.ObjmultusReadDIDOConfig.SoftwareVersion, 'ConfigVersion': self.ObjmultusReadDIDOConfig.ConfigVersion}
		return multusReadDIDO_pb2.multusReadDIDOVersions(**result)

	#######################################################################################
	def gRPCSetDigitalOutputs(self, request, context):
		print ("gRPCSetDigitalOutputs function called = Request: " + str(request) + " context: " + str(context))
		result = {'String': "dummy"}

		self.ObjmultusReadDIDOHandling.DOSet[0] = request.DI01
		self.ObjmultusReadDIDOHandling.DOSet[1] = request.DI02
		self.ObjmultusReadDIDOHandling.DOSet[2] = request.DI03
		self.ObjmultusReadDIDOHandling.DOSet[3] = request.DI04
		self.ObjmultusReadDIDOHandling.DOSet[4] = request.DI05
		self.ObjmultusReadDIDOHandling.DOSet[5] = request.DI06
		self.ObjmultusReadDIDOHandling.DOSet[6] = request.DI07
		self.ObjmultusReadDIDOHandling.DOSet[7] = request.DI08
		
		self.ObjmultusdTools.logger.debug ("Received gRPC update - Write out DO -- " + str(request.DI01) + ", " + str(request.DI02) + ", " + str(request.DI03) + ", " + str(request.DI04) + ", " + str(request.DI05) + ", " + str(request.DI06) + ", " + str(request.DI07) + ", " + str(request.DI08))
		self.ObjmultusReadDIDOHandling.ObjmultusHardware.writeDO(0, self.ObjmultusReadDIDOHandling.DOSet)
		return multusReadDIDO_pb2.EmptyRequestmultusReadDIDO(**result)

############################################################################################################
############################################################################################################

class multusReadDIDOOperateClass(object):
	def __init__(self, ObjmultusReadDIDOConfig, ObjmultusdTools):

		self.ObjmultusReadDIDOConfig = ObjmultusReadDIDOConfig
		self.ObjmultusdTools = ObjmultusdTools

		self.KeepThreadRunning = True

		self.ObjmultusHardware = multusHardwareHandler.multusHardwareHandlerClass(self.ObjmultusReadDIDOConfig, self.ObjmultusdTools)
		return

	def __del__(self):
		print ("leaving multusReadDIDOOperateClass")
		pass

	def Operate(self, multusdPingInterval, bPeriodicEnable, ModuleControlPort):

		## setup the periodic alive mnessage stuff
		periodic = None
		if bPeriodicEnable:
			print ("Setup the periodic Alive messages")
			TimestampNextmultusdPing = time.time()
			periodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', ModuleControlPort)
			if not periodic.ConnectFeedbackSocket():
				self.ObjmultusdTools.logger.debug("Stopping Process, cannot establish Feedback Connection to multusd")
				sys.exit(1)

		# declare a server object with desired number
		# of thread pool workers.
		self.gRPCServer = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

		self.ObjmultusReadDIDOHandling = ClassmultusReadDIDOHandling(self.ObjmultusReadDIDOConfig, self.ObjmultusdTools, self.ObjmultusHardware)
		#self.ObjOperatemultusReadDIDOThread.start()

		# setting up the gRPC Server
		multusReadDIDO_pb2_grpc.add_gRPCmultusReadDIDOServicer_to_server(gRPCmultusReadDIDOServicerClass(self.ObjmultusReadDIDOHandling ), self.gRPCServer)
 
		# bind the server to the port defined above
		self.gRPCServer.add_insecure_port('[::]:{}'.format(self.ObjmultusReadDIDOConfig.gRPCPort))
 
		# start the server
		self.gRPCServer.start()
		self.ObjmultusdTools.logger.debug('gRPCmultusReadDIDO Server running ...')

		# 2020-01-01
		# the loop shall not sleep longer than 1 second.. otherwise the handling in the stop procedure gets too slow
		SleepingTime = multusdPingInterval
		if multusdPingInterval > 1.0:
			SleepingTime = 1.0

		NextPeriodicTransfer = 0
		while self.KeepThreadRunning:
			
			Timestamp = time.time()
			if periodic and Timestamp >= TimestampNextmultusdPing:
				periodic.SendPeriodicMessage()
				TimestampNextmultusdPing = time.time() + multusdPingInterval
								
				if periodic.WeAreOnError:
					self.ObjmultusdTools.logger.debug("Error connecting to multusd... we stop running")
					self.KeepThreadRunning = False

			if self.ObjmultusReadDIDOConfig.ReadInDIEnable:
				print ("We read in all Digital Inputs at once")
				if self.ObjmultusReadDIDOConfig.ReadLastDOInsteadOfDI:
					self.ObjmultusReadDIDOHandling.DIStatus = self.ObjmultusReadDIDOHandling.ObjmultusHardware.ReadStatusOfDos(0)
				else:
					self.ObjmultusReadDIDOHandling.DIStatus = self.ObjmultusReadDIDOHandling.ObjmultusHardware.readDI(0)

				if self.ObjmultusReadDIDOHandling.DIStatusOld != self.ObjmultusReadDIDOHandling.DIStatus or NextPeriodicTransfer < Timestamp:
					self.ObjmultusReadDIDOHandling.TransferStatusToRemote(self.ObjmultusReadDIDOHandling.DIStatus)
					NextPeriodicTransfer = Timestamp + self.ObjmultusReadDIDOConfig.TransferInterval
					self.ObjmultusReadDIDOHandling.DIStatusOld = self.ObjmultusReadDIDOHandling.DIStatus

			if self.KeepThreadRunning:
				time.sleep (SleepingTime)

		return
