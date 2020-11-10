# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2019-11-11
#
# runs a controlport, which fires an error if the controlport is not 
# touched peridically
#
import socket
import time
import threading
import select

class ClassControlPortThread(threading.Thread):

	def __init__(self, Module, multusdConfig, ObjmultusdTools):
	
		self.ThreadName = ObjmultusdTools.ControlPortThreadSuffix + Module.ModuleParameter.ModuleIdentifier
		# initialize the 2 parent classes
		#threading.Thread.__init__(self, name = self.ThreadName)
		super(ClassControlPortThread, self).__init__(name = self.ThreadName)
		#self._stop_event = threading.Event()

		self.Module = Module
		self.ObjmultusdTools = ObjmultusdTools

		self.ObjmultusdTools.logger.debug("Started up multusdControlPortThread.ClassControlPortThread Thread " + self.ThreadName + " Task ident: " + str(threading.current_thread().ident))

		self.ControlPortNeverConnected = True
	
		self.bTimeout = False
		self.connection	= None

		# 2020-01-22
		self.TimestampNextSelectReturnExpectedOffset = 0.05
		self.TimestampNextSelectReturnExpected = 0.0

		## At Startup we can wait up to 15.0 seconds longer, than normally
		self.StartupOffset = 15.0

		return

	def __del__(self):
		print ("Thread: " + self.ThreadName + " shutting Down")
		return

	def stop(self):
		print ("Thread: " + self.ThreadName + " StopEvent forced")
		bError = False
		try:
			if self.connection:

				print ("Thread: " + self.ThreadName + " we close our TCP Connection")
				self.connection.close()

			print ("Thread: " + self.ThreadName + " we Shutdown the socket")
			self.ServerSocket.shutdown(socket.SHUT_RDWR)
			print ("Thread: " + self.ThreadName + " we close the socket")
			self.ServerSocket.close()
		except:
			print ("Thread: " + self.ThreadName + " Error while shutting down the listening socket")
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error Thread: " + self.ThreadName + ": " + ErrorString)
			bError = True
		#self._stop_event.set()
		
		return bError

	def __CreateListeningSocket__(self, Host, Port, Timeout):

		# Create a TCP/IP socket
		self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		# Bind the socket to the port
		server_address = ('localhost', Port)
		print ("Thread: " + self.ThreadName + " starting listening up on: " + server_address[0] + " port: " + str(server_address[1]))
		self.ServerSocket.bind(server_address)

		# Listen for incoming connections
		## 0 means to accept only one connection at time
		self.ServerSocket.listen(1)

		# if the socket is non blocking, the select will return immediatly and consume a lot of processor power
		self.ServerSocket.setblocking(True)

		self.socks = [self.ServerSocket]

	def __CleanupSocksList__(self, SocketToKeep = 0, KeepTheHighest = False):
		i = len(self.socks) - 1
		HighestIndex = i
		## We only want to delete the connections in the array, but not the root socket
		while i >= 0 and self.socks[i]:
			if ((KeepTheHighest and i != HighestIndex and i != SocketToKeep) or (not KeepTheHighest and i != SocketToKeep)):
				print ("Cleanup Examining Socket in list: " + str(self.socks[i]))
				if self.socks[i].fileno() <= 0:
					print ("Cleanup delete Socket in list: " + str(self.socks[i]))
					del self.socks[i]
				else:
					try:
						self.ObjmultusdTools.logger.debug("X Cleanup Close Socket in list: " + str(self.socks[i]))
						self.socks[i].close()
						print ("X Cleanup delete Socket in list after closing: " + str(self.socks[i]))
						del self.socks[i]
					except:
						print ("X Unknown Error operating on socket connection.. we proceed")

			i = i - 1	
		return

	def DoTimoutForcedProcedure(self):
		# First we call the Fail-Safe function
		self.Module.Thread.ObjFailSafeFunctions.SetIntoFailSafeState(False)

		# Then we stop the process
		# within the stop procedure a second fail-safe procedure call is done
		self.Module.Thread.ProcessIsRunning = self.Module.Thread.StopSingleProcess(self.Module.ModuleParameter, self.Module.Thread.ProcessIsRunning)

		return;

	def run(self):

		self.__CreateListeningSocket__('localhost', self.Module.ModuleParameter.ModuleControlPort, self.Module.ModuleParameter.ModuleControlMaxAge)

		while getattr(self.Module.ControlThread, "do_run", True):

			SelectTimeout = self.Module.ModuleParameter.ModuleControlMaxAge + self.StartupOffset
			## no hanging in the accept, if the process is not running
			if self.Module.Thread and self.Module.Thread.StartProcess and self.Module.Thread.ProcessIsRunning and not self.Module.Thread.StopProcess and not self.Module.Thread.ReloadProcess and not self.Module.Thread.NoStartupAllowedProcessIsInStrangeState and not self.Module.Thread.Shutdown:

				## we need this initialisation otherwise it can come to an never ending loop 
				TimestampLatestReceive = time.time() + SelectTimeout
				while not self.bTimeout and getattr(self.Module.ControlThread, "do_run", True) and not self.Module.Thread.Shutdown and not self.Module.Thread.ReloadProcess:
					
					## We look at too many connections..
					## All connections more than the one which is really needed will be closed
					## If someone connects to our FB Socket, this connection will be checked too and this may cause problems..

					self.__CleanupSocksList__(SocketToKeep = 0, KeepTheHighest = True)
					"""
					i = 0
					for fd in self.socks:
						print ("Filedescriptors given to select: " +str(i) + ": " + str(fd))
						i = i + 1
					"""

					# 2020-01-22
					# Important for watchdog trigger
					self.TimestampNextSelectReturnExpected = time.time() + SelectTimeout + self.TimestampNextSelectReturnExpectedOffset
		
					#if self.Module.ModuleParameter.ModuleIdentifier == "multusOLI":
					#print ("Select with Timout: " + str(SelectTimeout))
					readable,_,_ = select.select(self.socks,[],[], SelectTimeout)
					
					if not readable:
						TheTimeItTook = time.time() - TimestampLatestReceive
						self.ObjmultusdTools.logger.debug("Error Thread: " + self.ThreadName + " TIMEOUT Sockets, there is nothing readable .... we break .. Time since last Reading: " + str(TheTimeItTook) + " s")
						self.bTimeout = True
						break
					else:	
						for SingleSocket in readable:
							## maybe we have to connect first
							if(SingleSocket == self.ServerSocket):
								try: 
									self.connection, client_address = self.ServerSocket.accept()
									self.socks.append(self.connection)
				
									self.ControlPortNeverConnected = False

									self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " connection from " + client_address[0] + ":" + str(client_address[1]))
								except:
									self.bTimeout = True
									break
									
							else:
								try: 
									data = SingleSocket.recv(1)

									if data:
										TimestampReceived = time.time()
										TheTimeItTook = TimestampReceived - TimestampLatestReceive
										TimestampLatestReceive = TimestampReceived
										#print ("Thread: " + self.ThreadName + " received: " + str(data) + " Time: " + str(TheTimeItTook) + " s")

									#Check whether the timespan between the receives, even if there had notheing been received
									# has been overextended.. and then.. 
									else:
										TimestampReceived = time.time()
										TheTimeItTook = TimestampReceived - TimestampLatestReceive
										if TheTimeItTook > SelectTimeout:
											self.ObjmultusdTools.logger.debug("Error Thread: " + self.ThreadName + " received NO Data: " + str(data) + " Time: " + str(TheTimeItTook) + " s")
											self.bTimeout = True
											break

								except: 
									self.bTimeout = True
									break

						SelectTimeout = self.Module.ModuleParameter.ModuleControlMaxAge
					## End while select loop

				if self.bTimeout:
					self.TimestampNextSelectReturnExpected = 0.0
					if not self.Module.Thread.Shutdown and not self.Module.Thread.ReloadProcess:
						self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " We got a timout.. we execute the FailSafe functions and Stopp the corresponding Process immediatly")
						self.DoTimoutForcedProcedure()
		
					#We rest the Timout Variable to make the whole thing continue
					self.bTimeout = False


				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " No more messages.. we close connection") 
				try:
					if self.connection:
						self.connection.close()
				except:
					pass
				## cleanup the socks array
				self.__CleanupSocksList__()

			else:
				# waiting for process to come up an connect
				time.sleep(0.5)
				
		print("ControlThread: Stopping " + self.getName() + " thread.")

		return
