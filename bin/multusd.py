#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2019-10-30
#
# multusd
#
# the multusd is quite similar to the systemd.
# ist is the systemd for the multus routines and services
#
# Read in /usr/local/etc/multus/php/BasicInfos.conf
# Get the multusModulesConfig Paremeter
#
# Read in the Modules config..
# get the enabled modules and their startup routines
#
# furthermore keep them running and check the update directory on changes
#
#

import sys
import os
import shutil
import time
import signal
import stat
import pathlib

sys.path.append('/multus/lib')
import libpidfile
import multusdModuleConfig
import multusdModuleHandling
import multusdConfig
import multusdTools
import multusdControlPortThread
import multusdService

class ClassOperateModules(object):

	def __init__(self):
		print ("multusd: starting ClassOperateModules")

		# first we get the config of our own process
		self.multusdConfig = multusdConfig.ConfigDataClass()
		self.multusdConfig.readConfig()
		
		#then we start a tools instance
		self.ObjmultusdTools = multusdTools.multusdToolsClass()

		## Initialize logging...
		self.ObjmultusdTools.InitGlobalLogging(self.multusdConfig.LogFile)
		
		try:
			self.multusdIsRunningTwice = False
			with(libpidfile.PIDFile(self.multusdConfig.PIDFile)):
				print ("multusd: Writing PID File: " + self.multusdConfig.PIDFile)
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)
			self.multusdIsRunningTwice = True
			sys.exit(1)

		## Now e get the configuration of the single modules, the multusd should handle 
		self.multusdModulesConfig = multusdModuleConfig.ClassModuleConfig(self.multusdConfig)
		## read separatly
		self.multusdModulesConfig.ReadModulesConfig()
		self.CheckOndBNKEnabled()

		self.UpdateDirectory = self.ObjmultusdTools.multusdTMPDirectory + "/system"

		if os.path.exists(self.UpdateDirectory):
			## starting up.. old stuff is not from interest then
			shutil.rmtree(self.UpdateDirectory,  ignore_errors = True)
	
		os.mkdir(self.UpdateDirectory)
		os.chmod(self.UpdateDirectory,stat.S_IRWXU |stat.S_IRWXG | stat.S_IRWXO)

		self.multusdServicesThreads = list()
		
		self.RebootAfterStopping = False

		# initialize the signal handler
		signal.signal(signal.SIGTERM, self.__handler__)
		signal.signal(signal.SIGINT, self.__handler__)

		## period of time after then a restart is allowed
		self.ThreadShouldRunAtLeast = 60.0 

		self.bContinueCheckingOfThreads = True

		# 2020-01-22
		if self.multusdConfig.GeneralHWWatchdogIsEnabled:
			self.HWWatchdogIsEnabled = False
			self.TriggerWatchdogEnable = True
			import multusHardwareHandler
			self.ObjmultusHardware = multusHardwareHandler.multusHardwareHandlerClass(self.multusdConfig, self.ObjmultusdTools)

		self.ObjmultusdTools.logger.debug("Started up, initializing finished")

		return

	############################################################################################################
	def __del__(self):
		
		try:
			if not self.multusdIsRunningTwice:
				os.remove(self.multusdConfig.PIDFile)
		except:
			ErrorString = self.ObjmultusdTools.FormatException()
			self.ObjmultusdTools.logger.debug("Error: " + ErrorString)


		print ("multusd: exiting ClassOperateModules .. all threads had been stoped")
		
		if self.RebootAfterStopping:
			os.system("/sbin/reboot")

		#self.ObjmultusdTools.logger.debug("Stopped")
		return

	############################################################################################################
	def __handler__(self, signum, frame):
		
		print ('multusd: Signal handler called with signal: ' + str(signum) + "\n")
		if signum == signal.SIGTERM or signum == signal.SIGINT:
			
			self.bContinueCheckingOfThreads = False
			
			print ("multusd: please wait... shutting all threads down\n")

	############################################################################################################
	def __StopAllThreads__(self):

		self.DisableHWWatchdog()

		## 2019-12-04
		## For the first moment, we tell the Threads that we are in shutdown mode
		for ServiceModule in self.multusdModulesConfig.EnabledServicesModules:
			# Command to stop the real OS System covered by this thread
			if ServiceModule.Thread:
				ServiceModule.Thread.Shutdown = True
				# Command to stop the real OS System covered by this thread
				ServiceModule.Thread.StopProcess = True

		## After they know this.. we stop every single process and shut down the threads
		for ServiceModule in self.multusdModulesConfig.EnabledServicesModules:
			# look for a controlPort Thread.. we may have to stop it first
			if ServiceModule.ModuleParameter.ModuleControlPortEnabled and ServiceModule.ControlThread:
				## With that sleep the process has finished surely the TCP connection to the multusd
				time.sleep(0.5)

				print ("multusd: We shut down Thread: " + ServiceModule.ControlThread.ThreadName)
				ServiceModule.ControlThread.do_run = False
				time.sleep(0.5)

				## the thread may hang in accept listen socket
				## We force closing of the socket
				ServiceModule.ControlThread.stop()
			
			# Then we ensure, that the corresponding processes had been shut down
			TimeLoopToEnd = time.time() + ServiceModule.ModuleParameter.MaxTimeWaitForShutdown
			while ServiceModule.Thread and ServiceModule.Thread.CheckStatusSingleProcess(ServiceModule.ModuleParameter) and time.time() < TimeLoopToEnd:
				time.sleep(0.2)

			## OK, process is dead.. we stop the thread itself
			if ServiceModule.Thread:
				print ("multusd: We shut down Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier)
				ServiceModule.Thread.stop()
				ServiceModule.Thread.do_run = False

			## After the process is surely dead, we join the controlThread
			if ServiceModule.ModuleParameter.ModuleControlPortEnabled and ServiceModule.ControlThread:
				try:
					ServiceModule.ControlThread.join()
				except:
					ErrorString = self.ObjmultusdTools.FormatException()
					self.ObjmultusdTools.logger.debug("Error at join() shutting down ControlThread for " + ServiceModule.ModuleParameter.ModuleIdentifier + " : " + ErrorString)

			if ServiceModule.Thread:
				try:
					ServiceModule.Thread.join()
				except:
					ErrorString = self.ObjmultusdTools.FormatException()
					self.ObjmultusdTools.logger.debug("Error at join() shutting down Thread for " + ServiceModule.ModuleParameter.ModuleIdentifier + " : " + ErrorString)

		return 
    
	############################################################################################################
	def __StartSingleControlThread__(self, ServiceModule):
		## If there is a ControlPortThread, we first start the control Port thread
		if self.bContinueCheckingOfThreads and ServiceModule.ModuleParameter.ModuleControlPortEnabled:

			ServiceModule.ControlThread = multusdControlPortThread.ClassControlPortThread(ServiceModule, self.multusdConfig, self.ObjmultusdTools)
			ServiceModule.ControlThread.start()
			if ServiceModule.ControlThread.is_alive():
				self.ObjmultusdTools.logger.debug("multusd: Started Instance of ControlThread: " + ServiceModule.ControlThread.getName() + " successfully")
				ServiceModule.ControlThreadLastTimeStarted = time.time()
			else:
				self.ObjmultusdTools.logger.debug("multusd: Faild to start Instance of ControlThread for Process: " + ServiceModule.ModuleParameter.ModuleIdentifier)

		return

	############################################################################################################
	def __StartSingleThread__(self, ServiceModule):
		"""

		:type ServiceModule: object
		"""
		if self.bContinueCheckingOfThreads:

			ServiceModule.Thread = multusdService.ClassmultusdThread(ServiceModule, self.multusdConfig, self.ObjmultusdTools)
			ServiceModule.Thread.start()

			if ServiceModule.Thread.is_alive():
				## Now we start the process from the thread
				ServiceModule.Thread.StopProcess = False
				ServiceModule.Thread.ReloadProcess = False
				ServiceModule.Thread.StartProcess = True

				self.ObjmultusdTools.logger.debug("multusd: Started Instance of thread: " + ServiceModule.Thread.getName() + " successfully \n")
				ServiceModule.ThreadLastTimeStarted = time.time()
			else:
				self.ObjmultusdTools.logger.debug("multusd: Failed to start thread for Module: " + ServiceModule.ModuleParameter.ModuleIdentifier)

		return

	############################################################################################################
	def __StartAllThreads__(self):
		## First we do an object for every single service we got

		for ServiceModule in self.multusdModulesConfig.EnabledServicesModules:
			self.__StartSingleControlThread__(ServiceModule)	
			self.__StartSingleThread__(ServiceModule)	
				
		time.sleep(2.0)

		self.EnableHWWatchdog()
		return

	############################################################################################################
	def __CheckUpdateDirectory__(self):
		## communication happens mainly via the touch of a command-file
		##
		## there are several comamnd files
		
		Action = None

		AgeReloadFileHasToHave = 60.0

		## Reboot.0
		## Reboot.300
		## Reload.Modules -- whcih means to stop all modules and reload everything
		ReloadFile = self.UpdateDirectory + "/Reload.Modules"
		Reboot0 = self.UpdateDirectory + "/Reboot.0"
		Reboot300 = self.UpdateDirectory + "/Reboot.300"

		if (os.path.isfile(ReloadFile)):
			## 2021-02-08
			## the Reload file has to exist and it schould be older than a given time... then we do a relaod
			ObjReloadFile = pathlib.Path(ReloadFile)
			TimeFileLatestModified = ObjReloadFile.stat().st_mtime	
			if TimeFileLatestModified < (time.time() - AgeReloadFileHasToHave):
				Action = "Reload.Modules"
				self.ObjmultusdTools.logger.debug("Reload of all modules requested")
				os.remove(ReloadFile)

		if (os.path.isfile(Reboot0)):
			Action = "Reboot.0"
			self.RebootAfterStopping = True
			self.ObjmultusdTools.logger.debug("Immediate Reboot requested")
			os.remove(Reboot0)

		if (os.path.isfile(Reboot300)):
			self.RebootAfterStopping = True
			Action = "Reboot.300"
			self.ObjmultusdTools.logger.debug("Reboot in 300 seconds requested")
			os.remove(Reboot300)

		return Action

	############################################################################################################
	# 2019-11-26
	def __CheckProcessorTemperatureIsValid__(self, ValidityState):
		#print ("Check on processor temperature is enabled: " + str(self.multusdConfig.ProcessorTemperatureEnabled))
		if self.multusdConfig.ProcessorTemperatureEnabled:
			ProcessorTemperatureIsValid = False
			
			CPUTemp = self.multusdConfig.ProcessorMaxTemperature + 1.0

			# Read in the processor temperature
			try:
				TempFile = open(self.multusdConfig.ProcessorTemperatureFile)  
				CPUTemp = float(TempFile.read())/1000.0
				TempFile.close()  
			except:
				ErrorString = self.ObjmultusdTools.FormatException()
				# we log only once
				if ValidityState:
					self.ObjmultusdTools.logger.debug("Fatal Error reading Processor temperature: " + ErrorString)
					self.ObjmultusdTools.logger.debug("Fatal Error reading in Processor Temperature.. we assume " + str(CPUTemp))
				
			ProcessorTemperatureIsNotTooLow = (CPUTemp >= self.multusdConfig.ProcessorMinTemperature) 

			Hysteresistemp = self.multusdConfig.ProcessorMaxTemperature - self.multusdConfig.ProcessorCoolDownHysteresis

			ProcessorTemperatureIsNotTooHigh = not ProcessorTemperatureIsNotTooLow or (((CPUTemp <= self.multusdConfig.ProcessorMaxTemperature) and ValidityState) or ((CPUTemp < Hysteresistemp) and not ValidityState)) 

			# just became too high
			if not ProcessorTemperatureIsNotTooHigh and ValidityState and ProcessorTemperatureIsNotTooLow:
				self.ObjmultusdTools.logger.debug("Processor Temperature is too high: " + str(CPUTemp) + " Maximum allowed temperature:" + str(self.multusdConfig.ProcessorMaxTemperature) + " Waiting for cool down")
			# Temp had been to high, but coold down sufficiently 
			elif ProcessorTemperatureIsNotTooHigh and not ValidityState and ProcessorTemperatureIsNotTooLow:
				self.ObjmultusdTools.logger.debug("Processor Temperature low enough: " + str(CPUTemp) + " The Hysteresis Temperature is " + str(Hysteresistemp) + " We go on")
				ProcessorTemperatureIsValid = True
			# standard.. we run
			elif ProcessorTemperatureIsNotTooHigh and ProcessorTemperatureIsNotTooLow:
				ProcessorTemperatureIsValid = True
			# dropped under Min
			elif not ProcessorTemperatureIsNotTooLow and ValidityState:
				self.ObjmultusdTools.logger.debug("Processor Temperature is too low: " + str(CPUTemp) + " Minimum temperature:" + str(self.multusdConfig.ProcessorMinTemperature) + " Waiting for heating up")
		else:
			ProcessorTemperatureIsValid = True

		return ProcessorTemperatureIsValid

	############################################################################################################
	def CheckOndBNKEnabled(self):
		dBNKEnabled = False

		for Mod in self.multusdModulesConfig.EnabledServicesModules:
			if Mod.ModuleParameter.ModuleIdentifier == "multusdBNK" and Mod.ModuleParameter.Enabled:
				dBNKEnabled = True
				break
			elif Mod.ModuleParameter.ModuleIdentifier == "OLIIntegrity" and Mod.ModuleParameter.Enabled:
				dBNKEnabled = True
				break

		for Mod in self.multusdModulesConfig.EnabledServicesModules:
			Mod.dBNKEnabled = dBNKEnabled

		return
	############################################################################################################
	## 2020-01-22
	def EnableHWWatchdog(self):
		if self.multusdConfig.GeneralHWWatchdogIsEnabled:
			self.ObjmultusdTools.logger.debug("multusd: Enable Hardware Watchdog")
			self.ObjmultusHardware.EnableHWWatchdog()
			self.HWWatchdogIsEnabled = True
		return

	def DisableHWWatchdog(self):
		if self.multusdConfig.GeneralHWWatchdogIsEnabled:
			self.ObjmultusdTools.logger.debug("multusd: Disable Hardware Watchdog")
			self.ObjmultusHardware.DisableHWWatchdog()
			self.HWWatchdogIsEnabled = False
		return

	def TriggerHWWatchdog(self):
		if self.multusdConfig.GeneralHWWatchdogIsEnabled and self.HWWatchdogIsEnabled and self.TriggerWatchdogEnable:
			#print ("TRigger HW Watchdog")
			self.ObjmultusHardware.TriggerHWWatchdog()

			## 2020-06-25
			## 200ms Watchdog.. 250ms delay make system crash
			#time.sleep(0.25)
		return

	############################################################################################################
	def RunServices(self):
		print ("multusd: Entered run services function\n");

		ProcessorTemperatureIsValid = True
		ProcessorTemperatureIsValidOld = True
		Action = None
		RebootTimer = time.time()
	
		# Now e sturt up the needed threads
		ProcessorTemperatureIsValid = self.__CheckProcessorTemperatureIsValid__(ProcessorTemperatureIsValid)
		ProcessorTemperatureIsValidOld = ProcessorTemperatureIsValid
		if ProcessorTemperatureIsValid:
			self.__StartAllThreads__()
		else:
			self.ObjmultusdTools.logger.debug("Processor Temperature is too high not starting up the processes")

		RunningAction = None
		## go into an endless loop checking the threads
		while self.bContinueCheckingOfThreads and Action != "Reboot.0" and RunningAction != "Reboot.0":

			## First we check the temperature of the processor.. is it in a valid range
			ProcessorTemperatureIsValid = self.__CheckProcessorTemperatureIsValid__(ProcessorTemperatureIsValid)
			if not ProcessorTemperatureIsValid and ProcessorTemperatureIsValidOld:
				self.ObjmultusdTools.logger.debug("Processor Temperature is too high we stop all processes")
				ProcessorTemperatureIsValidOld = ProcessorTemperatureIsValid
				self.__StopAllThreads__()
			elif ProcessorTemperatureIsValid and not ProcessorTemperatureIsValidOld:
				self.ObjmultusdTools.logger.debug("Processor Temperature cooled down we start up all processes again")
				ProcessorTemperatureIsValidOld = ProcessorTemperatureIsValid

				## do a clean startup and read in the config again..
				## this also frees the memory used by the old threads
				self.multusdModulesConfig.ReadModulesConfig()
				self.CheckOndBNKEnabled()

				self.__StartAllThreads__()

			## The we have a look at possible actions
			if Action == 'Reboot.300':
				RebootTimer = time.time() + 300.0
				RunningAction = 'Reboot.counting'
				self.ObjmultusdTools.logger.debug("For reboot in 300 secs we start counting down.. we will shutdown at : " + str(RebootTimer))

			elif RunningAction == 'Reboot.counting' and time.time() > RebootTimer:
				RunningAction = 'Reboot.0'

			elif Action == 'Reload.Modules':
				# If the temperature is too hight, the processes must have been stopped already
				if ProcessorTemperatureIsValid:
					self.__StopAllThreads__()
					print ("Stopping of all threads and processes done.. ")

				if ProcessorTemperatureIsValid:
					## Reread the nwe config
					self.multusdModulesConfig.ReadModulesConfig()
					self.CheckOndBNKEnabled()
					self.__StartAllThreads__()
				else:
					print ("We wait restarting the processes.. till the temperature is low enough")
				
				Action = None

			## We start with a sleep
			if ProcessorTemperatureIsValid:
				# with the watchdog enabled we cannot sleep so much
				self.TriggerHWWatchdog()
				time.sleep(0.08)
				self.TriggerHWWatchdog()

				for ServiceModule in self.multusdModulesConfig.EnabledServicesModules:
				
					## We first check the ControlThread
					Timestamp = time.time()
					if self.bContinueCheckingOfThreads and ServiceModule.ModuleParameter.ModuleControlPortEnabled and not ServiceModule.ControlThread.is_alive():
						try:
							if not ServiceModule.ControlThreadErrorLoggingDone:
								self.ObjmultusdTools.logger.debug("multusd: Control-Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " is not running")
							
							if ((ServiceModule.ControlThreadLastTimeStarted + self.ThreadShouldRunAtLeast) < time.time()):
								self.ObjmultusdTools.logger.debug("multusd: We have to restart Control Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier)
								# first we join the gone thread
								ServiceModule.ControlThread.join()
								self.__StartSingleControlThread__(ServiceModule)	
								ServiceModule.ControlThreadErrorLoggingDone = False
								
								# Ensuring, that the process is running
								if ServiceModule.Thread:
									ServiceModule.Thread.StartProcess = True
							else:
								if not ServiceModule.ControlThreadErrorLoggingDone:
									self.ObjmultusdTools.logger.debug("multusd: Control Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " Respawing too fast.. we wait and kill the corresponding process")
									self.ObjmultusdTools.logger.debug("multusd: Control Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " Thread had been started: " + str(ServiceModule.ControlThreadLastTimeStarted) + "should run at least: " + str(self.ThreadShouldRunAtLeast) + " Had actually Run: " + str(time.time() - ServiceModule.ControlThreadLastTimeStarted))

									ServiceModule.ControlThreadErrorLoggingDone = True

								## One reason for the too fast Respawnig could be a problem with the control socket.. let's kill the corresponding Process
								# 2020-12-28
								if ServiceModule.Thread and ServiceModule.Thread.ProcessIsRunning:
									ServiceModule.Thread.StopProcess = True

						except:
							ErrorString = self.ObjmultusdTools.FormatException()
							self.ObjmultusdTools.logger.debug("multusd: Error Starting ControlThread: " + ErrorString)

					# 2020-01-22
					# check whether all select timings are done right
					# HWWatchdog related
					elif self.bContinueCheckingOfThreads \
					and ServiceModule.Thread \
					and ServiceModule.ControlThread \
					and ServiceModule.Thread.ProcessIsRunning \
					and ServiceModule.ModuleParameter.ModuleControlPortEnabled \
					and ServiceModule.ControlThread.TimestampNextSelectReturnExpected > 0.0 \
					and ServiceModule.ControlThread.TimestampNextSelectReturnExpected < Timestamp \
					and not ServiceModule.ControlThread.bTimeout \
					and not ServiceModule.Thread.Shutdown \
					and not ServiceModule.Thread.ReloadProcess:
						
						## 2021-01-25
						## calls SW Watchdog ... the child process seems to be doomed and all the select seems to hang
						if not ServiceModule.Thread.ForceSWWatchdogProcedure:
							self.ObjmultusdTools.logger.debug("multusd: XXXL Fatal Error ControlThread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " took too long.. overlap (s):  " + str(Timestamp - ServiceModule.ControlThread.TimestampNextSelectReturnExpected) + " SW Watchdog functionality called .. we force stopping child process")

							ServiceModule.Thread.ForceSWWatchdogProcedure = True

						if self.multusdConfig.GeneralHWWatchdogIsEnabled:
							## TODO
							## 2020-07-24
							## not working corectly, the timing is measured unsuitable
							#self.TriggerWatchdogEnable = False
							pass
							#self.ObjmultusdTools.logger.debug("multusd: XXXL Fatal Error ControlThread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " took too long.. overlap (s):  " + str(Timestamp - ServiceModule.ControlThread.TimestampNextSelectReturnExpected))


					if self.bContinueCheckingOfThreads and not ServiceModule.Thread.is_alive():
						try: 
							if not ServiceModule.ThreadErrorLoggingDone:
								self.ObjmultusdTools.logger.debug("multusd: Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " is not running")
							
							if ((ServiceModule.ThreadLastTimeStarted + self.ThreadShouldRunAtLeast) < time.time()):
								self.ObjmultusdTools.logger.debug("multusd: We have to restart Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier)
								# first we join the gone thread
								ServiceModule.Thread.join()
								self.__StartSingleThread__(ServiceModule)	
								ServiceModule.ThreadErrorLoggingDone = False

							else:
								if not ServiceModule.ThreadErrorLoggingDone:
									self.ObjmultusdTools.logger.debug("multusd: Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " Respawing too fast.. We wait")
									self.ObjmultusdTools.logger.debug("multusd: Thread: " + ServiceModule.ModuleParameter.ModuleIdentifier + " Thread had been started: " + str(ServiceModule.ThreadLastTimeStarted) + "should run at least: " + str(self.ThreadShouldRunAtLeast) + " Had actually Run: " + str(time.time() - ServiceModule.ThreadLastTimeStarted))
									ServiceModule.ThreadErrorLoggingDone = True

						except:
							ErrorString = self.ObjmultusdTools.FormatException()
							self.ObjmultusdTools.logger.debug("multusd: Error Starting Thread: " + ErrorString)

				## OK.. we have checked the threads.. no we look for updates from the PHP interface in the update directory
				Action = self.__CheckUpdateDirectory__()
			else:
				# in case the temperature is too high.. we could take a longer sleep, but the HW Watchdog needs to be triggered
				self.TriggerHWWatchdog()
				time.sleep(0.08)
				self.TriggerHWWatchdog()

			## End Valid ProcessorTemperature

		# We left the While loop.. because of Reboot going on
		self.__StopAllThreads__()

		return

############################################################################################################
if __name__ == "__main__":

	Operate = ClassOperateModules()

	Operate.RunServices()
