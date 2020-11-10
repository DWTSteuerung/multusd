# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2019-11-10
#
# functions for sending periodic datagrams to the multusd 
# process to indicate the whole process is still running
#

import socket
import sys
import os

class ClassControlSocketClient(object):
	def __init__(self, ObjmultusdTools, Host, Port):
		self.ObjmultusdTools = ObjmultusdTools	

		# Connect the socket to the port where the server is listening
		self.ServerAddress = (Host, Port)

		self.WeAreOnError = False
		self.WeAreOnErrorOld = self.WeAreOnError
		return

	def ConnectFeedbackSocket(self):
		Success = False

		try:
			# Create a TCP/IP socket
			self.ObjmultusdTools.logger.debug(str(os.getpid()) + " We create our Socket und connect to the multusd Feedback Socket: " + str(self.ServerAddress))
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect(self.ServerAddress)
			self.ObjmultusdTools.logger.debug(str(os.getpid()) + " We are connected to the multusd Feedback Socket: " + str(self.ServerAddress))
			Success = True
			self.WeAreOnError = False
			if self.WeAreOnErrorOld != self.WeAreOnError:
				self.ObjmultusdTools.logger.debug(str(os.getpid()) + " After Error ... Connecting to Feedback Socket succeeded")
				self.WeAreOnErrorOld = self.WeAreOnError
		except:
			self.WeAreOnError = True
			if self.WeAreOnErrorOld != self.WeAreOnError:
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug(str(os.getpid()) + " Problems connecting to multusd FB Socket: " + ErrorString)
				self.WeAreOnErrorOld = self.WeAreOnError

		return Success


	def __del__(self):
		print ("Exiting Object: ClassControlSocketClient")
		try:
			self.ObjmultusdTools.logger.debug(str(os.getpid()) + " We close our Feedback socket")
			self.sock.close()
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug(str(os.getpid()) + " Error closing FB Socket: " + ErrorString)
			
		return


	def SendPeriodicMessage(self):
		try:
			print ("connecting to " + str(self.ServerAddress[0]) + " + port: " + str(self.ServerAddress[1]))
			self.sock.sendall(bytes(1))
			self.WeAreOnError = False
			if self.WeAreOnErrorOld != self.WeAreOnError:
				self.ObjmultusdTools.logger.debug(str(os.getpid()) + " After Error sending periodic messages succeeded again")
				self.WeAreOnErrorOld = self.WeAreOnError
		
		except:
			self.WeAreOnError = True
			if self.WeAreOnErrorOld != self.WeAreOnError:
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug(str(os.getpid()) + " Error sending periodic messages: " + ErrorString)
				self.WeAreOnErrorOld = self.WeAreOnError
		return


