# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2019-11-28
# 
# classes to request network status by gRPC
#

import time
import grpc
import sys

sys.path.append('/multus/lib')
import libmultusLANWANCheck
import libOpenVPNCheck
import multusdConfig
import multusdModuleConfig

sys.path.append('/multus/lib/proto')
import LANWANOVPNCheck_pb2
import LANWANOVPNCheck_pb2_grpc

############################################################################################################
# Class doing Network requests
class gRPCLANWANStatusClass(object):
	def __init__(self, ObjmultusdTools):

		self.LogginEnable = True

		self.ObjmultusdTools = ObjmultusdTools
	
		# first we get the config of the multusd system
		ObjmultusdConfig = multusdConfig.ConfigDataClass()
		ObjmultusdConfig.readConfig()
		
		## after we got the modules init file.. we have to read it, to get the config files for this process
		ObjmultusdModulesConfig = multusdModuleConfig.ClassModuleConfig(ObjmultusdConfig)
		ObjmultusdModulesConfig.ReadModulesConfig()

		Ident = "multusLANWANCheck"
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				self.ObjmultusLANWANCheckConfig = libmultusLANWANCheck.multusLANWANCheckConfigClass(Module.ModuleParameter.ModuleConfig)
				self.ObjmultusLANWANCheckConfig.ReadConfig()
				break

		## 2020-01-01
		## We neet some additional information from the Module multusLAN
		AuxIdent = "multusLAN"
		#WalkThe list of modules to find our configuration files.. 
		for Module in ObjmultusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == AuxIdent:
				self.ObjmultusLANWANCheckConfig.ReadInmultusLANConfig(Module.ModuleParameter.ModuleConfig)
				break

		## gRPC specific Stuff
		self.host = 'localhost'
		self.server_port = self.ObjmultusLANWANCheckConfig.WANCheckResultPort

		# gRPC Stuff needed lateron
		self.LANWANChannel = None
		self.LANWANstub = None
		self.ConnectionStatus = False
		self.TimestampLatestErrorOccured = None

		return

	# function can be used to force a refresh of the connection, which is normally done by the gRPC Stuff itself
	def gRPCSetupLANWANConnection(self, bForce = False):
		if self.LANWANChannel == None or self.LANWANstub == None or bForce:
			self.ObjmultusdTools.logger.debug("Setup the LANWAN Check connection freshly")
			del(self.LANWANChannel)
			del(self.LANWANstub)

			# instantiate a communication channel
			self.LANWANChannel = grpc.insecure_channel('{}:{}'.format(self.host, self.server_port))

			# bind the client to the server channel
			self.LANWANstub = LANWANOVPNCheck_pb2_grpc.gRPCServiceStub(self.LANWANChannel)

			## because of logging we start with True
			self.ConnectionStatus = True

	def GetmultusLANWANCheckProcessStatus(self):
		Response = LANWANOVPNCheck_pb2.ProcessStatusMessagemultusLANWANCheck()
		Response.ProcessOK = False
		if self.LANWANstub == None:
			self.gRPCSetupLANWANConnection()

		gRPCRequestMessage = LANWANOVPNCheck_pb2.EmptyRequestmultusLANWANCheck(String = "Empty")
		try: 
			Response = self.LANWANstub.gRPCGetmultusLANWANCheckStatus(gRPCRequestMessage)
			self.ConnectionStatus = True
		except:
			if self.ConnectionStatus:
				self.ConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC multusLANWANCheck Process Status Error: " + ErrorString)

		return Response, self.ConnectionStatus

	def GetLANStatus(self, message = "Hallo"):
		Response = LANWANOVPNCheck_pb2.ResponseMessage()
		Response.ConnectionStatus = False
		Response.ValidStatus = False
		
		if self.LANWANstub == None:
			self.gRPCSetupLANWANConnection()

		gRPCRequestMessage = LANWANOVPNCheck_pb2.RequestMessage(RequestMessageMemberString = message)
		try: 
			Response = self.LANWANstub.gRPCGetLANStatus(gRPCRequestMessage)
			self.ConnectionStatus = True
		except:
			if self.ConnectionStatus:
				self.ConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC LAN Status Error: " + ErrorString)

		return Response, self.ConnectionStatus

	def GetWANStatus(self, message = 'Hallo'):
		Response = LANWANOVPNCheck_pb2.ResponseMessage()
		Response.ConnectionStatus = False
		Response.ValidStatus = False

		if self.LANWANstub == None:
			self.gRPCSetupLANWANConnection()

		if not self.ObjmultusLANWANCheckConfig.NoWANEnable and self.ObjmultusLANWANCheckConfig.WANCheckEnable:
			gRPCRequestMessage = LANWANOVPNCheck_pb2.RequestMessage(RequestMessageMemberString = message)

			try:
				Response = self.LANWANstub.gRPCGetWANStatus(gRPCRequestMessage)
				self.ConnectionStatus = True
			except:
				if self.ConnectionStatus:
					self.ConnectionStatus = False
					self.TimestampLatestErrorOccured = time.time()

					if self.LogginEnable:
						ErrorString = self.ObjmultusdTools.FormatException()
						self.ObjmultusdTools.logger.debug("gRPC WAN Status Error: " + ErrorString)
		## 2021-02-14
		## if not enabled.. we return True
		else:
			Response.ConnectionStatus = True
			Response.ValidStatus = True

		return Response, self.ConnectionStatus

############################################################################################################
# Class doing OVPN requests
class gRPCOVPNStatusClass(object):
 
	def __init__(self, ObjmultusdTools):

		self.LogginEnable = True

		self.ObjmultusdTools = ObjmultusdTools

		# first we get the config of the multusd system
		ObjmultusdConfig = multusdConfig.ConfigDataClass()
		ObjmultusdConfig.readConfig()
		
		## after we got the modules init file.. we have to read it, to get the config files for this process
		multusdModulesConfig = multusdModuleConfig.ClassModuleConfig(ObjmultusdConfig)
		multusdModulesConfig.ReadModulesConfig()

		Ident = "OpenVPNCheck"
		for Module in multusdModulesConfig.AllModules:
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				self.ObjmultusOVPNConfig = libOpenVPNCheck.multusOVPNConfigClass(Module.ModuleParameter.ModuleConfig)
				self.ObjmultusOVPNConfig.ReadConfig()
				break

		self.host = 'localhost'
		self.server_port = self.ObjmultusOVPNConfig.OVPNCheckResultPort

		# gRPC Stuff needed lateron
		self.OVPNChannel = None
		self.OVPNstub = None
		self.OVPNConnectionStatus = False
		self.TimestampLatestErrorOccured = 0.0

		return

	# function can be used to force a refresh of the connection, which is normally done by the gRPC Stuff itself
	def gRPCSetupOVPNConnection(self, bForce = False):
		if self.ObjmultusOVPNConfig.OVPNCheckEnable and (self.OVPNChannel == None or self.OVPNstub == None or bForce):
			self.ObjmultusdTools.logger.debug("Setup the OVPN Check connection freshly")
			del(self.OVPNChannel)
			del(self.OVPNstub)

			# instantiate a communication channel
			self.OVPNChannel = grpc.insecure_channel('{}:{}'.format(self.host, self.server_port))

			# bind the client to the server channel
			self.OVPNstub = LANWANOVPNCheck_pb2_grpc.gRPCServiceStub(self.OVPNChannel)

			## because of logging we start with True
			self.OVPNConnectionStatus = True

	def GetmultusOVPNProcessStatus(self):
		Response = LANWANOVPNCheck_pb2.ProcessStatusMessagemultusLANWANCheck()
		Response.ProcessOK = False
		if self.OVPNstub == None:
			self.gRPCSetupOVPNConnection()

		gRPCRequestMessage = LANWANOVPNCheck_pb2.EmptyRequestmultusLANWANCheck(String = "Empty")
		try: 
			Response = self.OVPNstub.gRPCGetmultusLANWANCheckStatus(gRPCRequestMessage)
			self.OVPNConnectionStatus = True
		except:
			if self.OVPNConnectionStatus:
				self.OVPNConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC multusOVPN Process Status Error: " + ErrorString)

		return Response, self.OVPNConnectionStatus

	def GetOVPNStatus(self, message = 'Hallo'):
		Response = LANWANOVPNCheck_pb2.ResponseMessage()
		Response.ConnectionStatus = False
		Response.ValidStatus = False

		if self.OVPNstub == None:
			self.gRPCSetupOVPNConnection()

		if self.ObjmultusOVPNConfig.OVPNCheckEnable:
			gRPCRequestMessage = LANWANOVPNCheck_pb2.RequestMessage(RequestMessageMemberString = message)

			try:
				Response = self.OVPNstub.gRPCGetOVPNStatus(gRPCRequestMessage)
				self.OVPNConnectionStatus = True
			except:
				if self.OVPNConnectionStatus:
					self.OVPNConnectionStatus = False
					self.TimestampLatestErrorOccured = time.time()

					if self.LogginEnable:
						ErrorString = self.ObjmultusdTools.FormatException()
						self.ObjmultusdTools.logger.debug("gRPC OVPN Status Error: " + ErrorString)

		## 2021-02-14
		## if not enabled.. we return True
		else:
			Response.ConnectionStatus = True
			Response.ValidStatus = True

		return Response, self.OVPNConnectionStatus

