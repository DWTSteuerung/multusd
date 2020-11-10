# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2020-09-25
#
# TODO
# implement the Json Config stuff also here... if nedded
# 
# classes to request multusReadDIDO status by gRPC
#

import time
import grpc
import sys
import pprint

sys.path.append('/multus/lib/proto')
import multusReadDIDO_pb2
import multusReadDIDO_pb2_grpc

############################################################################################################
# Class doing multusReadDIDO requests
class gRPCmultusReadDIDOStatusClass(object):
	def __init__(self, ObjmultusdTools, Hostname, gRPCPort):

		self.ObjmultusdTools = ObjmultusdTools
	
		## gRPC specific Stuff
		self.host = Hostname
		self.server_port = gRPCPort

		# gRPC Stuff needed lateron
		self.multusReadDIDOChannel = None
		self.multusReadDIDOstub = None
		self.ConnectionStatus = False
		self.TimestampLatestErrorOccured = None

		return

	# function can be used to force a refresh of the connection, which is normally done by the gRPC Stuff itself
	def gRPCSetupmultusReadDIDOConnection(self, bForce = False):
		if self.multusReadDIDOChannel == None or self.multusReadDIDOstub == None or bForce:
			self.ObjmultusdTools.logger.debug("Setup the multusReadDIDO Check connection freshly")
			del(self.multusReadDIDOChannel)
			del(self.multusReadDIDOstub)

			# instantiate a communication channel
			self.multusReadDIDOChannel = grpc.insecure_channel('{}:{}'.format(self.host, self.server_port))

			# bind the client to the server channel
			self.multusReadDIDOstub = multusReadDIDO_pb2_grpc.gRPCmultusReadDIDOStub(self.multusReadDIDOChannel)

			# because of logging, we start with True
			self.ConnectionStatus = True

	def GetmultusReadDIDOProcessStatus(self):
		Response = multusReadDIDO_pb2.ProcessStatusMessagemultusReadDIDO()
		Response.ProcessOK = False

		if self.multusReadDIDOstub == None:
			self.gRPCSetupmultusReadDIDOConnection()

		gRPCRequestMessage = multusReadDIDO_pb2.EmptyRequestmultusReadDIDO(String = "Empty")
		try: 
			Response = self.multusReadDIDOstub.gRPCGetmultusReadDIDOStatus(gRPCRequestMessage)
			self.ConnectionStatus = True
		except:
			if self.ConnectionStatus:
				self.ConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC multusReadDIDO Process Status Error: " + ErrorString)

		return Response, self.ConnectionStatus

	
	def SetDigitalOutputs(self, gRPCRequestMessage):
		Response = multusReadDIDO_pb2.EmptyRequestmultusReadDIDO

		print ("Status to transfer: ")
		pprint.pprint(gRPCRequestMessage)

		if self.multusReadDIDOstub == None:
			self.gRPCSetupmultusReadDIDOConnection()

		try: 
			Response = self.multusReadDIDOstub.gRPCSetDigitalOutputs(gRPCRequestMessage)
			self.ConnectionStatus = True
		except:
			if self.ConnectionStatus:
				self.ConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC multusReadDIDO Status Error: " + ErrorString)

				"""
				if ErrorString.find("StatusCode.UNIMPLEMENTED") >= 0:
					print("We got this stupid UNIMPLEMENTED Error we reconnect")
					self.gRPCSetupmultusReadDIDOConnection(bForce = True)
				"""

		return self.ConnectionStatus

	def getmultusReadDIDOVersions(self):
		Response = multusReadDIDO_pb2.multusReadDIDOVersions
		Response.SoftwareVersion = None
		Response.ConfigVersion = None

		if self.multusReadDIDOstub == None:
			self.gRPCSetupmultusReadDIDOConnection()

		gRPCRequestMessage = multusReadDIDO_pb2.EmptyRequestmultusReadDIDO(String = "Empty")
		try: 
			Response = self.multusReadDIDOstub.gRPCgetmultusReadDIDOVersions(gRPCRequestMessage)
			self.ConnectionStatus = True
		except:
			if self.ConnectionStatus:
				self.ConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC multusReadDIDO Status Error: " + ErrorString)
	
		return Response, self.ConnectionStatus
