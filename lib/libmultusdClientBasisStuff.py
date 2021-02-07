# -*- coding: utf-8 -*-
# 
# 2021-02-07
# Karl Keusgen
#
# all that periodically executed stuff for the controlling of the multusd child processes
#
# we handle the control port as well as the control file timestamp update
#
##
import sys
import time
sys.path.append('/multus/lib')
import multusdControlSocketClient

class multusdClientBasisStuffClass(object):
	def __init__(self, ObjConfig, ObjmultusdTools):
		self.ObjmultusdTools = ObjmultusdTools
		self.ObjConfig = ObjConfig

		self.KeepThreadRunning = True
		self.multusdPingInterval = 5.0
		self.ObjPeriodic = None
		return

	############################################################
	def SetupPeriodicmessages(self, bPeriodicmultusdSocketPingEnable):
		bSuccess = False

		MaxSleepingTime = 1.0
		SleepingTime = MaxSleepingTime
		
		try:
			## We do the peridic stuff 5 times per period, so we get it right when checking it
			self.multusdPingInterval = self.ObjConfig.ModuleControlMaxAge / 5.0

			## setup the periodic alive mnessage stuff
			if bPeriodicmultusdSocketPingEnable:
				self.ObjmultusdTools.logger.debug("Setup the periodic Alive messages")
				self.TimestampNextmultusdPing = time.time()
				self.ObjPeriodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', self.ObjConfig.ModuleControlPort)
				if not self.ObjPeriodic.ConnectFeedbackSocket():
					self.ObjmultusdTools.logger.debug("Stopping Process, cannot establish Feedback Connection to multusd")
					sys.exit(1)

			# 2021-01-31 
			# do the touch thing to check alive status even if no control socket is activated
			if self.ObjConfig.ModuleControlFileEnabled:
				## maybe we do the checking only by timstamp of PID file and not by control port
				if not self.ObjPeriodic:
																										# dummy parameters
					self.ObjPeriodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', 888)
				
				## initialize the timspamp based stuff
																				## We do it twice as often as required, to ease the checking
				self.ObjPeriodic.InitCheckByThouch(self.ObjConfig.LPIDFile, (self.ObjConfig.ModuleControlMaxAge / 5.0))
				## We do the first check right here.. might be better after a shutdown by 9
				self.ObjPeriodic.DoCheckByTouch(time.time())

			# 2020-01-01
			# the loop shall not sleep longer than 1 second.. otherwise the handling in the stop procedure gets too slow
			SleepingTime = self.multusdPingInterval
			if self.multusdPingInterval > MaxSleepingTime:
				SleepingTime = MaxSleepingTime

			bSuccess = True

		except:
			ErrorString = self.ObjmultusdTools.FormatException()	
			self.ObjmultusdTools.logger.debug("SetupPeriodicmessages Fatal error setting up perodic stuff -- bPeriodicmultusdSocketPingEnable: " + str(bPeriodicmultusdSocketPingEnable))
			self.ObjmultusdTools.logger.debug("SetupPeriodicmessages Fatal error setting up perodic stuff: " + ErrorString)

		return SleepingTime, bSuccess 

	############################################################
	def DoPeriodicMessage(self, bPeriodicmultusdSocketPingEnable):
		bSuccess = True
		Timestamp = time.time()

		## first we do the control port stuff and talk to the multud
		if bPeriodicmultusdSocketPingEnable and self.ObjPeriodic:
			if Timestamp >= self.TimestampNextmultusdPing:
				self.ObjPeriodic.SendPeriodicMessage()
				self.TimestampNextmultusdPing = time.time() + self.multusdPingInterval
				
			if self.ObjPeriodic.WeAreOnError:
				self.ObjmultusdTools.logger.debug("Error connecting to multusd... we stop running")
				bSuccess = false

		# 2021-01-31
		# Addition do the PID file touch stuff as well
		# the multusd checks the timestamp of the PID file.. it should not be too old..
		if self.ObjPeriodic:
			self.ObjPeriodic.DoCheckByTouch(Timestamp)

		return bSuccess 

