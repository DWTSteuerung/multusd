# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2019-12-30
#
# Some tools handling OpenVPN processes
#

import os
import sys
import subprocess
import shlex
import time

class OVPNToolsClass(object):
	def __init__(self, ObjmultusOVPNConfig, ObjmultusdTools):
		self.OpenVPNPID = 0
		self.OpenVPNProcessRuns = False
	
		self.ObjmultusOVPNConfig = ObjmultusOVPNConfig
		self.ObjmultusdTools = ObjmultusdTools

		TmpPath = '/multus/tmp'
		self.OpenVPNPIDFile = TmpPath + '/' + self.ObjmultusOVPNConfig.Ident + '.PID'
		self.OpenVPNStatusFile = TmpPath + '/' + self.ObjmultusOVPNConfig.Ident + '.status'
		self.OpenVPNWorkDir = '/multus/openvpn'
		self.OpenVPNDaemon = self.ObjmultusOVPNConfig.Ident

		self.MaxAgeStatusFile = 120.0
		return

	def CleanupOldOVPNProcesses(self):
		self.GetOpenVPNPID()
		self.StopOpenVPNProcess()
		return

	def __del__(self):
		self.ObjmultusdTools.logger.debug ("leaving OVPNToolsClass terminate OVPNProcess")
		## 2020-08-10
		## we do this in the main class.. unreliable here
		#self.StopOpenVPNProcess()

		return

	def StartOVPNServerProcess(self):
		# The Server uses a different working directory
		OpenVPNWorkDir = self.OpenVPNWorkDir + "/" + self.ObjmultusOVPNConfig.Ident

		OVPNCall = shlex.split(self.ObjmultusOVPNConfig.OpenVPNBinary + ' --daemon ' + self.OpenVPNDaemon +' --writepid ' + self.OpenVPNPIDFile + ' --script-security 2 --status ' + self.OpenVPNStatusFile + ' 10 --cd ' + OpenVPNWorkDir + ' --config ' + self.ObjmultusOVPNConfig.OpenVPNConfig)

		RetVal = subprocess.check_call(OVPNCall)
		if RetVal == 0:
			self.OpenVPNProcessRuns = True
			self.ObjmultusdTools.logger.debug ("Started up VPNServerProcess sucessfully")
		else:
			self.ObjmultusdTools.logger.debug ("Failed starting up VPNServerProcess")

		return

	def StartOVPNClientProcess(self):
		OVPNCall = shlex.split(self.ObjmultusOVPNConfig.OpenVPNBinary + ' --writepid ' + self.OpenVPNPIDFile + ' --daemon ' + self.OpenVPNDaemon + ' --status ' + self.OpenVPNStatusFile + ' 10 --cd ' + self.OpenVPNWorkDir + ' --config ' + self.ObjmultusOVPNConfig.OpenVPNConfig)

		RetVal = subprocess.check_call(OVPNCall)
		if RetVal == 0:
			self.OpenVPNProcessRuns = True
			self.ObjmultusdTools.logger.debug ("Started up VPNClientProcess sucessfully")
		else:
			self.ObjmultusdTools.logger.debug ("Failed starting up VPNCLientProcess")

		return

	def GetOpenVPNPIDFromProcessList(self):
		## We look at the config.. first we get the Config Name
		A = self.ObjmultusOVPNConfig.OpenVPNConfig.split('/')
		OpenVPNConfig = A[len(A)-1]
		ps = subprocess.Popen("ps ax | grep " + OpenVPNConfig  + " | grep -v grep | grep -v gvim | awk '{print $1};'" , shell=True, stdout=subprocess.PIPE)
		output = ps.stdout.read()

		StrOutput = str(output) 
		#print (StrOutput)

		StrOutput = StrOutput.replace("b", "")

		StrOutput = StrOutput.replace("\\n", ";")
		#print (StrOutput)

		StrOutput = StrOutput.replace("'", "")
		#print (StrOutput)

		# remove the finishing ;
		StrOutput = StrOutput[:-1]
		#print (StrOutput)

		PIDList = StrOutput.split(';')

		#print(str(PIDList))	

		## check on singel PID
		SingleElement = False
		for PID in PIDList:
			L = len(PID)
			if L:
				SingleElement = True
				break

		if not SingleElement:
			PIDList.clear()
				
		return PIDList

	def GetOpenVPNPID(self):
		self.OpenVPNPID = 0
		try:
			with open(self.OpenVPNPIDFile, "r") as File:
				self.OpenVPNPID = int(File.read().strip())

			self.ObjmultusdTools.logger.debug ("We got PID from OVPNProcess: " + str(self.OpenVPNPID))
		except:
			pass
		return


	def CheckOpenVPNRunning(self):
		
		## We do a simple PING on the PID for the first tim
		try:
			os.kill(self.OpenVPNPID, 0)
			self.OpenVPNProcessRuns = True
		except:
			self.OpenVPNProcessRuns = False
			self.ObjmultusdTools.logger.debug ("ERROR Check on VPNProcess PID: " + str(self.OpenVPNPID) + " failed .. Process is not running")

		if self.OpenVPNProcessRuns:
			## detailled check on status file
			## if openvpn process hangs in a strange status.. the stat file may not be updated again... we check this
			Timestamp = time.time()
			MTimeStatFile = os.path.getmtime(self.OpenVPNStatusFile)
			MaximumTime = MTimeStatFile  + self.MaxAgeStatusFile
			if Timestamp > MaximumTime:
				self.ObjmultusdTools.logger.debug ("ERROR age of status file: " + self.OpenVPNStatusFile + " exceeds the maximum allowed do nothing time of: " + str(self.MaxAgeStatusFile))
				self.OpenVPNProcessRuns = False
		return 

	def StopOpenVPNProcess(self):
		StrangeError = False
		Kill0Failed = False
		if self.OpenVPNPID:
			try:
				os.kill(self.OpenVPNPID, 15)
			except:
				self.ObjmultusdTools.logger.debug ("ERROR .. sending SIGTERM to PID: " + str(self.OpenVPNPID) + " Maybe a dead PIDFile")
				StrangeError = True
			
			if StrangeError:
				## 2020-08-10
				## There is no OVPN Process running using the PID File, but there may be one using the config file.. we will find out
				PIDList = self.GetOpenVPNPIDFromProcessList()
				for PID in PIDList:
					try:
						self.ObjmultusdTools.logger.debug ("sending SIGTERM to PID: " + PID + " Got it from process list by ps")
						os.kill(int(PID), 15)
						self.OpenVPNPID = int(PID)
					except:
						self.ObjmultusdTools.logger.debug ("ERROR .. sending SIGTERM to PID: " + str(PID) + " Dont know")
						StrangeError = True
		
			if not StrangeError:
				MaxWaitTime = 2.0 
				TimstampTillWait = time.time() + MaxWaitTime
				while time.time() < TimstampTillWait and not Kill0Failed: 
					try:
						os.kill(self.OpenVPNPID, 0)
					except:
						Kill0Failed = True

					time.sleep(0.2)

				if not Kill0Failed:
					try:	
						os.kill(self.OpenVPNPID, 9)
					except:
						pass

				self.ObjmultusdTools.logger.debug("We stopped OpenVPn process with PID: " + str(self.OpenVPNPID))
				self.OpenVPNPID = 0
		return
