# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2019-12-30
#
# After changing the FailSafe technology 
#
import os
import sys
import time
import configparser

sys.path.append('/multus/lib')
## do the Periodic Alive Stuff
import libmultusdClientBasisStuff
import multusdBasicConfigfileStuff

import libOVPNTools

## now the protobuf stuff
import grpc
sys.path.append('/multus/lib/proto')
import multusOVPNClient_pb2
import multusOVPNClient_pb2_grpc
from concurrent import futures

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

class multusOVPNClientConfigClass(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):
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
			self.OpenVPNConfig = self.__assignStr__(config.get('OpenVPNConfig', 'Value'))
			self.OpenVPNEnable = self.__assignBool__(config.get('OpenVPNEnable', 'Value'))
			self.OpenVPNBinary = self.__assignStr__(config.get('OpenVPNBinary', 'Value'))
			self.gRPCPort = self.__assignInt__(config.get('gRPCPort', 'Value'))

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
							self.OpenVPNConfig = SingleInstance['OpenVPNConfig']
							self.OpenVPNEnable = bool(int(SingleInstance['OpenVPNEnable']))
							self.OpenVPNBinary = SingleInstance['OpenVPNBinary']
							self.gRPCPort = int(SingleInstance['gRPCPort'])

							break

						InstanceCounter += 1

			bSuccess = True
		except:
			ErrorString = ObjmultusdTools.FormatException()
			LogString = "Read in Json Process config failed with Error: " + ErrorString
			print(LogString)
			
		return bSuccess

#######################################################################################
# the real work is done here
#
class multusOVPNClientHandlingClass(object):
	def __init__(self, ObjmultusOVPNClientConfig, ObjmultusdTools):
		self.ObjmultusOVPNClientConfig = ObjmultusOVPNClientConfig 
		self.ObjmultusdTools = ObjmultusdTools

		## We create a Oject handling the OVPN Processes
		if self.ObjmultusOVPNClientConfig.OpenVPNEnable:
			self.ObjOVPNTools = libOVPNTools.OVPNToolsClass(self.ObjmultusOVPNClientConfig, self.ObjmultusdTools)
	
		self.ProcessHealthStatus = True

		## this variable is set by gRPC and termitaes the loop then
		self.gRPCKeepThreadRunning = True

		return

	def __del__(self):

		print ("Exiting multusOVPNClientHandlingClass")

		return

	def StartOVPN(self):
		#We start OpenVPN Process
		if self.ObjmultusOVPNClientConfig.OpenVPNEnable:
			self.ObjOVPNTools.CleanupOldOVPNProcesses()
			self.ObjOVPNTools.StartOVPNClientProcess()
			## Sometimes staring up takes some time
			time.sleep(1.0)
			self.ObjOVPNTools.GetOpenVPNPID()

		return

	def CheckOVPN(self):
		if self.ObjmultusOVPNClientConfig.OpenVPNEnable:
			self.ObjOVPNTools.CheckOpenVPNRunning()
			## if OVPN is not running, we terminate .. the multusd will restart us again and start the OVPN also
			self.gRPCKeepThreadRunning = self.ObjOVPNTools.OpenVPNProcessRuns 

		return

#######################################################################################
# this class operates the gRPC Requests
#
class gRPCmultusOVPNClientServicer(multusOVPNClient_pb2_grpc.gRPCmultusOVPNClientServicer):
	def __init__(self, ObjmultusdTools, ObjmultusOVPNClientHandling):
		self.ObjmultusdTools = ObjmultusdTools
		self.ObjmultusOVPNClientHandling = ObjmultusOVPNClientHandling
		return

	#######################################################################################
	def gRPCGetmultusOVPNClientStatus(self, request, contect):
		result= {'ProcessOK': self.ObjmultusOVPNClientHandling.ProcessHealthStatus}
		return multusOVPNClient_pb2.ProcessStatusMessagemultusOVPNClient(**result)

	#######################################################################################
	def gRPCRestartmultusOVPNClient(self, request, contect):
		# cause the termination of the endless loop .. restart by multusd
		self.ObjmultusdTools.logger.debug("gRPCRestartmultusOVPNClient called.... We stop now")

		self.ObjmultusOVPNClientHandling.gRPCKeepThreadRunning = False
		result= {'ProcessOK': self.ObjmultusOVPNClientHandling.ProcessHealthStatus}
		return multusOVPNClient_pb2.ProcessStatusMessagemultusOVPNClient(**result)

	#######################################################################################
	def gRPCgetmultusOVPNCheckVersions(self, request, context):
		result = {'SoftwareVersion': self.ObjmultusOVPNClientHandling.ObjmultusOVPNClientConfig.SoftwareVersion, 'ConfigVersion': self.ObjmultusOVPNClientHandling.ObjmultusOVPNClientConfig.ConfigVersion}
		return multusOVPNClient_pb2.multusOVPNCheckVersions(**result)

############################################################################################################
# Class called by the main programm
class multusOVPNClientOperateClass(libmultusdClientBasisStuff.multusdClientBasisStuffClass):
	def __init__(self, ObjmultusOVPNClientConfig, ObjmultusdTools):
		# init parent class
		libmultusdClientBasisStuff.multusdClientBasisStuffClass.__init__(self, ObjmultusOVPNClientConfig, ObjmultusdTools)

		self.ObjmultusOVPNClientConfig = ObjmultusOVPNClientConfig

		self.ObjmultusOVPNClientHandling = multusOVPNClientHandlingClass(ObjmultusOVPNClientConfig, ObjmultusdTools)
		
		return

	def __del__(self):
		print ("leaving multusOVPNClientOperateClass")
		pass

	############################################################
	###
	### main funtion running the main loop
	###
	#def RungRPCServer(self, multusdPingInterval, bPeriodicEnable, ModuleControlPort):
	def RungRPCServer(self, bPeriodicmultusdSocketPingEnable):
		## setup the periodic control stuff..
		## if this does not succeed .. we do not have to continue
		SleepingTime, self.KeepThreadRunning = self.SetupPeriodicmessages(bPeriodicmultusdSocketPingEnable)

		# declare a server object with desired number
		# of thread pool workers.
		self.gRPCServer = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
 
		# This line can be ignored
		multusOVPNClient_pb2_grpc.add_gRPCmultusOVPNClientServicer_to_server(gRPCmultusOVPNClientServicer(self.ObjmultusdTools, self.ObjmultusOVPNClientHandling), self.gRPCServer)
 
		# bind the server to the port defined above
		self.gRPCServer.add_insecure_port('[::]:{}'.format(self.ObjmultusOVPNClientConfig.gRPCPort))
 
		# start the server
		self.gRPCServer.start()
		self.ObjmultusdTools.logger.debug('multusOVPNClient gRPCService Server running ...')

		# Now we set up the OpenVPn connection
		self.ObjmultusOVPNClientHandling.StartOVPN()

		while self.KeepThreadRunning and self.ObjmultusOVPNClientHandling.gRPCKeepThreadRunning:
			## We do the periodic messages and stuff to indicate that we are alive for the multusd
			self.KeepThreadRunning = self.DoPeriodicMessage(bPeriodicmultusdSocketPingEnable)

			self.ObjmultusOVPNClientHandling.CheckOVPN()
	
			if self.KeepThreadRunning:
				time.sleep (SleepingTime)

		## We stop the OVPN Process
		if self.ObjmultusOVPNClientConfig.OpenVPNEnable:
			self.ObjmultusOVPNClientHandling.ObjOVPNTools.StopOpenVPNProcess()

		self.ObjmultusdTools.logger.debug('multsOVPNClient gRPCService Server Stopped ... self.KeepRunning: ' + str(self.KeepThreadRunning) + " OVPN ClientHandling KeepThreadRunning: " + str(self.ObjmultusOVPNClientHandling.gRPCKeepThreadRunning))

