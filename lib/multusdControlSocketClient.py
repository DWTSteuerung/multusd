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

		self.sock = None

		# Connect the socket to the port where the server is listening
		self.ServerAddress = (Host, Port)

		self.WeAreOnError = False
		self.WeAreOnErrorOld = self.WeAreOnError
		## 2021-01-30
		## send a message which can be calculated and checked
		self.Counter = 1

		## 2021-01-31
		## setup additional schecking b
		self.bCheckByTouchInitialized = False
		self.bFailureLOggingDone = False

		self.ObjmultusdTools.logger.debug(str(os.getpid()) + " Class: ClassControlSocketClient initialized ServerAdress: " + str(self.ServerAddress))

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
		if self.sock:
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
			self.sock.send(bytes([self.Counter]))
			self.WeAreOnError = False
			if self.WeAreOnErrorOld != self.WeAreOnError:
				self.ObjmultusdTools.logger.debug(str(os.getpid()) + " After Error sending periodic messages succeeded again")
				self.WeAreOnErrorOld = self.WeAreOnError

			if self.Counter < 9:
				self.Counter += 1
			else:
				self.Counter = 1

		except:
			self.WeAreOnError = True
			if self.WeAreOnErrorOld != self.WeAreOnError:
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug(str(os.getpid()) + " Error sending periodic messages: " + ErrorString)
				self.WeAreOnErrorOld = self.WeAreOnError
		return

	# 2021-01-31
	# added the functionality of touching and checking files as a way to furure out whether the process is still running
	# or not
	# to do this only by the socket thing may not be sufficient in all cases.. hard to believe, but processes can crash so 
	# strangely..

	# do the peridic touch on a file
	def InitCheckByThouch(self, TouchFile, Interval):
		import pathlib
		self.ObjTouchFile = pathlib.Path(TouchFile)
		self.Interval = Interval
		self.TimestampNextTouch = 0.0

		self.bFailureLOggingDone = False
		self.bCheckByTouchInitialized = True

	def DoCheckByTouch(self, Timestamp):
		if self.bCheckByTouchInitialized:
			if self.TimestampNextTouch < Timestamp:
				self.ObjTouchFile.touch()
				self.TimestampNextTouch = Timestamp + self.Interval

		elif not self.bFailureLOggingDone:
			self.ObjmultusdTools.logger.debug(str(os.getpid()) + " Error doing touch thing, because not initialized yet")
			self.bFailureLOggingDone = True
			
