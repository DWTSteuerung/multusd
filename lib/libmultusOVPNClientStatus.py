# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2020-01-12
# 
# classes to request multusOVPNClient status and restart OpenVPn connection by gRPC
#

import time
import grpc
import sys

sys.path.append('/multus/lib/proto')
import multusOVPNClient_pb2
import multusOVPNClient_pb2_grpc

############################################################################################################
# Class doing multusOVPNClient requests
class gRPCmultusOVPNClientStatusClass(object):
	def __init__(self, ObjmultusdTools):

		self.ObjmultusdTools = ObjmultusdTools

		# gRPC Stuff needed lateron
		self.multusOVPNClientChannel = None
		self.multusOVPNClientstub = None
		self.ConnectionStatus = False
		self.TimestampLatestErrorOccured = None

		return


	# function can be used to force a refresh of the connection, which is normally done by the gRPC Stuff itself
	def gRPCSetupmultusOVPNClientConnection(self, Host, Port):
		self.ObjmultusdTools.logger.debug("Setup the multusOVPNClient connection to: " + Host + ":" + str(Port) + " freshly")

		# instantiate a communication channel
		self.multusOVPNClientChannel = grpc.insecure_channel('{}:{}'.format(Host, Port))

		# bind the client to the server channel
		self.multusOVPNClientstub = multusOVPNClient_pb2_grpc.gRPCmultusOVPNClientStub(self.multusOVPNClientChannel)

	def GetmultusOVPNClientProcessStatus(self):
		Response = multusOVPNClient_pb2.ProcessStatusMessagemultusOVPNClient()
		Response.ProcessOK = False

		gRPCRequestMessage = multusOVPNClient_pb2.EmptyRequestmultusOVPNClient(String = "Empty")
		try: 
			Response = self.multusOVPNClientstub.gRPCGetmultusOVPNClientStatus(gRPCRequestMessage)
			self.ConnectionStatus = True
		except:
			if self.ConnectionStatus:
				self.ConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC multusOVPNClient Process Status Error: " + ErrorString)

		return Response, self.ConnectionStatus

	def gRPCRestartmultusOVPNClient(self):
		Response = multusOVPNClient_pb2.ProcessStatusMessagemultusOVPNClient()
		Response.ProcessOK = False

		gRPCRequestMessage = multusOVPNClient_pb2.EmptyRequestmultusOVPNClient(String = "Empty")
		try: 
			self.ObjmultusdTools.logger.debug("Do the Reset on the client")

			Response = self.multusOVPNClientstub.gRPCRestartmultusOVPNClient(gRPCRequestMessage)
			self.ConnectionStatus = True
		except:
			if self.ConnectionStatus:
				self.ConnectionStatus = False
				self.TimestampLatestErrorOccured = time.time()
				
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("gRPC multusOVPNClient Process Restart OpenVPN client Error: " + ErrorString)

		return Response, self.ConnectionStatus


