# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2019-11-02
#
# class definition operating a single service
#
# 2019-12-07
# Reworked it, so that one Class matches all processes
#

import os
import sys
import threading
import time
import importlib

sys.path.append('/multus/lib')
import multusdModuleHandling

class ClassmultusdThread(multusdModuleHandling.ClassRunModules, threading.Thread):

	def __init__(self, Module, multusdConfig, multusdTools):
		self.ThreadName = multusdTools.multusdServiceThreadSuffix + Module.ModuleParameter.ModuleIdentifier
		
		# initialize the 2 parent classes
		multusdModuleHandling.ClassRunModules.__init__(self, multusdTools, self.ThreadName)
		threading.Thread.__init__(self, name = Module.ModuleParameter.ModuleIdentifier)

		self.Module = Module
		self.multusdConfig = multusdConfig
		self.multusdTools = multusdTools
		
		## Init Logging in Module Class
		self.Module.InitLogging(self.ObjmultusdTools)

		self.PrepareUpdateDirectory(self.multusdTools.multusdTMPDirectory, self.Module.ModuleParameter.ModuleIdentifier)

		self.ObjmultusdTools.logger.debug("Started up multusdService.ClassmultusdThread Thread " + self.ThreadName + " Task ident: " + str(threading.current_thread().ident))
		self.FatalError = False
		self.ObjFailSafeFunctions = None

		# in case it is a native multusd process it has a controlport an we can load a extra class with fail-safe functions
		if self.Module.ModuleParameter.ModuleControlPortEnabled or self.Module.ModuleParameter.ModuleControlFileEnabled:
			try:
				## NOw we first have to build the name of the library for this module
				## 2019-12-30 .. in case we run several instances of 1 process.. we only need 1 libary identified by the BasicIndentifier Name
				Library = "lib" + self.Module.ModuleParameter.BasicIdentifier
				self.ObjmultusdTools.logger.debug("multusdService.ClassmultusdThread Thread " + self.ThreadName + " We add the library for Module " + self.Module.ModuleParameter.BasicIdentifier + " named: " + Library)
				DynamicComClass = importlib.import_module(Library)
				self.ObjmultusdTools.logger.debug("multusdService.ClassmultusdThread Thread " + self.ThreadName + " We imported library 	successfully:  Integrity Process multusdBNK/OLIIntegrity enabled: " + str(self.Module.DSVIntegrityEnabled))
				self.ObjFailSafeFunctions = DynamicComClass.FailSafeClass(self.multusdTools, self.Module.ModuleParameter.ModuleConfig, self.Module.ModuleParameter.ModuleIdentifier, self.Module.DSVIntegrityEnabled)
				self.ObjmultusdTools.logger.debug("multusdService.ClassmultusdThread Thread " + self.ThreadName + " Setup FailSafeClass successfully")
			except:
				self.FatalError = True
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("multusdService.ClassmultusdThread Thread " + self.ThreadName + " Fatal ERROR occured stting up the FailSafe Class: " + ErrorString)

		## 2021-01-31
		## Added PIDFile timstamp checking
		if self.Module.ModuleParameter.ModuleControlFileEnabled:
			self.InitVerifyAge(self.Module.ModuleParameter.ModulePIDFile)

		return

	def __del__(self):
		try:
			if self.ObjFailSafeFunctions and "ExecuteOnmultusdDie" in dir(self.ObjFailSafeFunctions):
				self.ObjFailSafeFunctions.ExecuteOnmultusdDie()
		except:
			pass
		return

	############################################################################################################
	def __DoJobBeforeStarting__(self, Module):
		Module.NextDataExpected = 0
		if self.ObjFailSafeFunctions:
			self.ObjFailSafeFunctions.SetIntoFailSafeState(self.ProcessIsRunning)
		return
	
	############################################################################################################
	def __DoJobBeforeReStarting__(self, Module):
		Module.NextDataExpected = 0
		if self.ObjFailSafeFunctions:
			self.ObjFailSafeFunctions.SetIntoFailSafeState(self.ProcessIsRunning)
		return

	############################################################################################################
	def __DoJobAfterStopping__(self, Module):
		Module.NextDataExpected = 0
		if self.ObjFailSafeFunctions:
			self.ObjFailSafeFunctions.SetIntoFailSafeState(self.ProcessIsRunning)
			self.ObjFailSafeFunctions.ExecuteAfterStop(self.ProcessIsRunning)
		return

	############################################################################################################
	def __DoJobAfterStarting__(self, Module):
		if self.ObjFailSafeFunctions:
			self.ObjFailSafeFunctions.ExecuteAfterStart(self.ProcessIsRunning)
		return

	############################################################################################################
	def run(self):
		"""
		# no more need to make the SleepingTime depending on the Refresh port.. it can go slow.. not problem, because only starting is affected
		if self.Module.ModuleParameter.ModuleControlMaxAge and self.Module.ModuleParameter.ModuleControlMaxAge < self.SleepingTime:
			self.SleepingTime = self.Module.ModuleParameter.ModuleControlMaxAge
		"""

		ReloadFile = self.UpdateDirectory + "/Reload"
		
		## Reset will be done before normal startup
		bResetDone = True

		while getattr(self.Module.Thread, "do_run", True) and not self.FatalError:

			if not self.ProcessIsRunning and not bResetDone:
				self.__DoJobBeforeStarting__(self.Module)
				bResetDone = True
			elif self.ProcessIsRunning and bResetDone:
				bResetDone = False

			# it the controlthread is in timeout.. we have to wait for the control-thread to finish its operations
			if (not self.Module.ControlThread or (self.Module.ControlThread and not self.Module.ControlThread.bTimeout)):
				self.__RunPeriodicJob__(self.Module)

				if self.ObjFailSafeFunctions:
					self.ObjFailSafeFunctions.ExecutePeriodic(self.ProcessIsRunning)
	
			## Check on Reload file in UPdate Directory
			if (os.path.isfile(ReloadFile)):
				self.ReloadProcess = True
				self.__DoJobBeforeReStarting__(self.Module)
				os.remove(ReloadFile)

			#print ("working on " + self.getName())
			time.sleep(self.SleepingTime)

		print("Stopping " + self.getName() + " thread.")
		

