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
# this class does th core of themultus:
# starting, stopping and checking of processes
#
import time
import sys
import os
import stat
import shutil
import subprocess

class ClassRunModules(object):

	def __init__(self, ObjmultusdTools, ThreadName):
		print ("starting ClassRunModules")
		self.ObjmultusdTools = ObjmultusdTools
		self.ThreadName = ThreadName
		
		self.ObjmultusdTools.logger.debug("Started up ClassRunModules Thread " + ThreadName)
	
		## these variables control the starting and stopping of the processes
		self.StartProcess = False
		self.StopProcess = False
		self.ReloadProcess = False

		self.Shutdown = False
		
		self.ProcessCheckSucceeded = True

		## Feedback
		self.ProcessIsRunning = False

		self.NextCheckToDo = time.time() + 30
		self.NextPIDStatusToDo = time.time() + 10

		self.UpdateDirectory = None

		## delay in process supervising loop
		## standard and maximum value
		self.SleepingTime = 1.0

		## 2021-01-24
		## SW Watchdog limitation
		self.ForceSWWatchdogProcedure = False
		return

	############################################################################################################
	def PrepareUpdateDirectory(self, multusdTMPDirectory, ModuleIdentifier):
		self.UpdateDirectory = multusdTMPDirectory + "/" + ModuleIdentifier

		try:
			if os.path.exists(self.UpdateDirectory):
				## starting up.. old stuff is not from interest then
				shutil.rmtree(self.UpdateDirectory,  ignore_errors = True)

			os.mkdir(self.UpdateDirectory)
			os.chmod(self.UpdateDirectory,stat.S_IRWXU |stat.S_IRWXG | stat.S_IRWXO)

		except:
			ErrorString = self.ObjmultusdTools.FormatException()	
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " PrepareUpdateDirectory Error" + ErrorString)
		
		return

	############################################################################################################
	def __del__(self):
		print ("exiting ClassRunModules")
	
		return

	############################################################################################################
	def stop(self):
		print ("multusdModuleHandling Called empty stop() function")
		return

	############################################################################################################
	def __DoJobBeforeReStarting__(self):
		print ("multusdModuleHandling Called empty __DoJobBeforeReStarting__() function")
		return

	############################################################################################################
	def __DoJobBeforeStarting__(self):
		print ("multusdModuleHandling Called empty __DoJobBeforeStarting__() function")
		return

	############################################################################################################
	def __DoJobAfterStarting__(self):
		print ("multusdModuleHandling Called empty __DoJobAfterStarting__() function")
		return

	############################################################################################################
	def __DoJobAfterStopping__(self):
		print ("multusdModuleHandling Called empty __DoJobAfterStopping__() function")
		return

	############################################################################################################
	#
	# sometimes the check against the PID file does not work.. we look up the process list
	# 2019-11-25
	#
	def __CheckOnProcessInPS__(self, ProcessBinary):
		ps = subprocess.Popen("ps ax | grep " + ProcessBinary + " | grep -v grep | grep -v gvim | awk '{print $1};'" , shell=True, stdout=subprocess.PIPE)
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

		return PIDList

	############################################################################################################
	## 2021-01-31
	###### Verify the corret age of a controlfile
	def InitVerifyAge(self, TouchFile):
		import pathlib
		self.ObjTouchFileV = pathlib.Path(TouchFile)

	def VerifyCorrectAgeOfTouchFile(self, ModuleControlMaxAge):
		bSuccess = False
		# We add a 100% security offset..
		MaxAge = time.time() - (2 * ModuleControlMaxAge)

		try:
			TimeFileLatestModified = self.ObjTouchFileV.stat().st_mtime
			if TimeFileLatestModified > MaxAge:
				bSuccess = True
				#print ("PID File Age ok: " + str(time.time() - TimeFileLatestModified) + " seconds")
			else:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Error on ControlFile it is too old: " + str(time.time() - TimeFileLatestModified) + " seconds")
		except:
			ErrorString = self.ObjmultusdTools.FormatException()	
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " VerifyCorrectAgeOfTouchFile Error" + ErrorString)
			pass

		return bSuccess

	############################################################################################################
	def __RunPeriodicJob__(self, Module):

		MaxTimeProcessStartCanTake = 30.0
		if Module.ControlThread:
			MaxTimeProcessStartCanTake = Module.ControlThread.StartupOffset

		Timestamp = time.time()

		# Starting a process
		if (not Module.ControlThread or (Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and self.StartProcess and not self.ProcessIsRunning and not self.ReloadProcess and not self.StopProcess and Timestamp > Module.ProcessTimestampToBeRestarted:

			## first we check, if the process is already running
			self.ProcessIsRunning = self.CheckStatusSingleProcess(Module.ModuleParameter)

			if not self.ProcessIsRunning:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 1 Run a process start procedure for Binary: " + Module.ModuleParameter.ModuleBinary)
				self.__DoJobBeforeStarting__()
				self.StartSingleProcess(Module.ModuleParameter)
				Module.ProcessLastTimeStarted = time.time()
				## We set this after the start.. because the start itself can take a very long time.. sometimes
				tProcessHasToBeStarted = time.time() + MaxTimeProcessStartCanTake

				## Check on the success of the starting procedure
				# on multusdJson we give a litte bit time, till process comes up.. 
				# fetching to config from the server, may take some time
				TestInterval = 5.0
				self.ObjmultusdTools.logger.debug("Check on start success of binary " + Module.ModuleParameter.ModuleBinary + " -- this can take up to " + str(MaxTimeProcessStartCanTake) + " seconds")
				while not self.ProcessIsRunning and time.time() < tProcessHasToBeStarted:
					self.ProcessIsRunning = self.CheckStatusSingleProcess(Module.ModuleParameter)
					if not self.ProcessIsRunning:
						time.sleep(TestInterval)

			if self.ProcessIsRunning:

				self.ObjmultusdTools.logger.debug("Binary " + Module.ModuleParameter.ModuleBinary + " is running now!")
				self.__DoJobAfterStarting__()
			else:
				## The process or whatever has to be killed...
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 2 Run a process start procedure Binary: " + Module.ModuleParameter.ModuleBinary + " Failed.. process seems not to be running.. we kill it again")
				self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)

				## We get a new startup time anyway.. can be an software error,, so 
				Module.DetermineNextStartupTime(self.ThreadName)
				Module.NextDataExpected = 0
				
		## 2021-01-24
		## the select in the contol thread may hang, if a child process is in a weird kill 9 condition.. so we setup
		## a Software Watchdog funtionality, which can be enabled by the main thread
		elif (not Module.ControlThread or (Module.ControlThread and not Module.ControlThread.bTimeout)) and self.ForceSWWatchdogProcedure:

			# First we call the Fail-Safe function
			## this call is a bit strange... but works
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " SW Watchdog: Set stalled process into failsafe state")
			Module.Thread.ObjFailSafeFunctions.SetIntoFailSafeState(False)

			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " SW Watchdog: Run a process stop procedure")
			self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)

			time.sleep (1.0)

			## reset the SW watchdog switch
			self.ForceSWWatchdogProcedure = False

		# stopping a process
		elif (not Module.ControlThread or (Module.ControlThread and not Module.ControlThread.bTimeout)) and self.StopProcess:
			self.StartProcess = False
			self.ReloadProcess = False

			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 2 Run a process stop procedure")
			
			self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)
			self.__DoJobAfterStopping__()

			self.StopProcess = False

			time.sleep (1.0)

			## Check on the success of the stopping procedure

		# restarting a process
		elif (not Module.ControlThread or (Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and self.ReloadProcess and self.StartProcess:
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 5 Run a process restart procedure " + Module.ModuleParameter.ModuleBinary)

			self.__DoJobBeforeReStarting__()
			self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)
			self.__DoJobAfterStopping__()

			self.StartSingleProcess(Module.ModuleParameter)
			Module.ProcessLastTimeStarted = time.time()
			## We set this after the start.. because the start itself can take a very long time.. sometimes
			tProcessHasToBeStarted = time.time() + MaxTimeProcessStartCanTake

			## Check on the success of the starting procedure
			while not self.ProcessIsRunning and time.time() < tProcessHasToBeStarted:
				self.ProcessIsRunning = self.CheckStatusSingleProcess(Module.ModuleParameter)
				if not self.ProcessIsRunning:
					self.ObjmultusdTools.logger.debug("Binary " + Module.ModuleParameter.ModuleBinary + " is still not running restart !!!!!!")
					time.sleep(2.0)	

			if self.ProcessIsRunning:
				self.ObjmultusdTools.logger.debug("Binary " + Module.ModuleParameter.ModuleBinary + " is finally running now !!!!!!")
				self.ReloadProcess = False
				self.__DoJobAfterStarting__()
			else:
				## The process or whatever has to be killed...
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 5 Run a process restart Failed.. we kill process again " + Module.ModuleParameter.ModuleBinary)
				self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)
				if not Module.ModuleParameter.ModuleControlPortEnabled:
					Module.DetermineNextStartupTime(self.ThreadName)

				Module.NextDataExpected = 0

		# Periodic Check by script, if there is one
		elif (not Module.ControlThread or (Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and Module.ModuleParameter.ModulePeriodicCheckEnabled and (self.NextCheckToDo < time.time()):
			#print ("Thread: " + self.ThreadName + " 6 Want to run a process check procedure and get the status by a script.. if there is one")
			self.ProcessCheckSucceeded = self.__CheckSingleProcess__(Module.ModuleParameter.ModuleCheckScript)
			self.NextCheckToDo = time.time() + Module.ModuleParameter.ModulePeriodicCheckInterval
			if not self.ProcessCheckSucceeded:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Error: CHecking Module " + Module.ModuleParameter.ModuleIdentifier + " Failure is not running well.. we force a restart")
				self.ReloadProcess = True
				
			# In the End, after the CHecking Process was done, we check the status
			self.ProcessIsRunning = self.CheckStatusSingleProcessByScript(Module.ModuleParameter.ModuleStatusScript, Module.ModuleParameter.ModuleStatusScriptParameter)

		## the Status Check by PID from PIDFile is done independently, if a regular Check is also done
		# periodic check against the PID kill 0
		##
		## 2021-02-07
		## We do this check even though the PID File check is disabled.. if so, we do it by ps
		if self.ProcessIsRunning and (not Module.ControlThread or (Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and (self.NextPIDStatusToDo < time.time()): # and Module.ModuleParameter.ModuleStatusByPIDFileEnable:
			#print ("Want to run ")
			# In the End, after the CHecking Process was done, we check the status
			self.ProcessIsRunning = self.CheckStatusSingleProcess(Module.ModuleParameter)
			if not self.ProcessIsRunning:
				# First we call the Fail-Safe function.. in case ther are some
				if Module.Thread and Module.Thread.ObjFailSafeFunctions:
					self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " kill 0 on PID failed: Set stalled process into failsafe state")
					Module.Thread.ObjFailSafeFunctions.SetIntoFailSafeState(False)

				## Make sure the process is dead
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " kill 0 on PID failed: Run a process stop procedure")
				self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter)

				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 6 Run a process PID Check Failed.. " + Module.ModuleParameter.ModuleBinary)
				## if the control-port is enabled.. we do the caclculation on next startup in the control port thread
				if not Module.ModuleParameter.ModuleControlPortEnabled:
					Module.DetermineNextStartupTime(self.ThreadName)

				Module.NextDataExpected = 0

			## Next check on PID file
			self.NextPIDStatusToDo = time.time() + Module.ModuleParameter.ModuleStatusByPIDFilePeriod

		## 2021-01-31
		## added timstamp check on the PID file
		## We do this only in case that the regular control thread did not realize anything yet
		## The same as the SW Watchdog
		if Module.ModuleParameter.ModuleControlFileEnabled and self.ProcessIsRunning and (not Module.ControlThread or (Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown:

			#We do the checking of the control file 60 seconds after upstarting the process
			if Timestamp > (Module.ProcessLastTimeStarted + 60.0): 
				bAgeOfControlFileSufficient = self.VerifyCorrectAgeOfTouchFile(Module.ModuleParameter.ModuleControlMaxAge)
				if not bAgeOfControlFileSufficient:
					## something went wrong... 
					## We kill the process if still running ...
				
					# First we call the Fail-Safe function.. in case ther are some
					if Module.Thread and Module.Thread.ObjFailSafeFunctions:
						self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Age checking on PID file age failed: Set stalled process into failsafe state")
						Module.Thread.ObjFailSafeFunctions.SetIntoFailSafeState(False)

					self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Age checking on PID file failed: Run a process stop procedure")
					self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)

					## if the control-port is enabled.. we do the caclculation on next startup in the control port thread
					if not Module.ModuleParameter.ModuleControlPortEnabled:
						Module.DetermineNextStartupTime(self.ThreadName)

					Module.NextDataExpected = 0
				
					time.sleep (1.0)

		return

	############################################################################################################
	def StartSingleProcess(self, ModuleParameter):
		
		if ModuleParameter.ModuleBinaryStartupDirectlyEnable:
			Binary = ModuleParameter.ModuleBinaryPath + "/" + ModuleParameter.ModuleBinary
			#print ("StartSingleProcess: Executing: " + Binary + " Parameter: " + ModuleParameter.ModuleBinaryParameter)
			subprocess.call([Binary, ModuleParameter.ModuleBinaryParameter], stdout=subprocess.DEVNULL)
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Starting Process Executing: " + Binary + " " + ModuleParameter.ModuleBinaryParameter)
			## We wait for Process to come up and write the PIDFile, otherwise the check if it is runing will fail
			time.sleep(1.0)
			
		elif ModuleParameter.ModuleStartScript:
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StartSingleProcess: Executing: " + ModuleParameter.ModuleStartScript + " " + ModuleParameter.ModuleStartScriptParameter)
			subprocess.call([ModuleParameter.ModuleStartScript, ModuleParameter.ModuleStartScriptParameter], stdout=subprocess.DEVNULL)

		return

	############################################################################################################
	def __StopProcessByPS__(self,  ModuleParameter, ProcessIsRunning):
		PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
		Len = len(PIDList)
		if Len and PIDList[0]:
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " We got several processes of binary " + ModuleParameter.ModuleBinary + " running with PIDs: " + str(PIDList) + " kill them all with 15")
			for PID in PIDList:
				try:
					os.kill(int(PID), 15)
				except:
					## got an error .. may be dead in the meantime?
					pass
			
			time.sleep(2)
			## Check once again, if there are still some processes
			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			Len = len(PIDList)
			if Len and PIDList[0]:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " We still got several processes of binary " + ModuleParameter.ModuleBinary + " running with PIDs: " + str(PIDList) + " kill them with 9")
				for PID in PIDList:
					try:
						os.kill(int(PID), 9)
						## succeeded .. then it must been dead
						ProcessIsRunning = False
					except:
						## Strange... process may be dead in the meantime.. we check on it again below
						pass
			else:
				ProcessIsRunning = False

			## We check finally, if there is something in the process list of this name .. we may have crashed somewhere before
			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			Len = len(PIDList)
			if not Len:
				ProcessIsRunning = False
		else:
			ProcessIsRunning = False

		return ProcessIsRunning 	

	############################################################################################################
	def StopSingleProcess(self, ModuleParameter, ProcessIsRunning = True):
		def EvalProcessIsRunnig(ModuleParameter):
			ProcessRuns = False
			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			if len(PIDList) and len(PIDList[0]):	
				ProcessRuns = True

			return ProcessRuns

		if ModuleParameter.ModuleBinaryStartupDirectlyEnable:
			pid = 0
			TimeToFinish = time.time() + ModuleParameter.MaxTimeWaitForShutdown

			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Stopping Process: " + ModuleParameter.ModuleBinary)

			if not os.path.exists(ModuleParameter.ModulePIDFile):
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- PID File not existant Process does not seem to run we look at the process list via ps command")
				ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)
			else:
				pid = 0
				try:
					with open(ModuleParameter.ModulePIDFile, "r") as f:
						StrPID = f.read().strip()
						pid = int(StrPID)

				except:
					pid = 0
					self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- Error reading PID in -- we read: " + StrPID)
					ErrorString = self.ObjmultusdTools.FormatException()	
					self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- Readin PID File Error: " + ErrorString)
					pass

				if pid:
					try:
						os.kill(pid, 15)

						time.sleep (1.0)
						ProcessIsRunning = EvalProcessIsRunnig(ModuleParameter)

					except:
						self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- kill 15 on PID " + str(pid) + " did not succeed: Process seems not to be running we go for it via ps comamnd")
						ErrorString = self.ObjmultusdTools.FormatException()	
						self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- kill 15 Error: " + ErrorString)

						ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)
						time.sleep (1.0)
						pass
				else:
					ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)
			
			# 2020-06-01
			while TimeToFinish > time.time() and ProcessIsRunning:
				ProcessIsRunning = EvalProcessIsRunnig(ModuleParameter)
				time.sleep(0.1)
									
			## Now we make it real sure, that the process is gone
			if not ProcessIsRunning:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- Process has been successfyully killed with signal 15")
			else:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- Process is still running we kill em finally with 9")
		
				if pid:
					try:
						os.kill(pid, 9)
						time.sleep(1)

						## We killed the process, now we check if it is still running
						ProcessIsRunning = self.CheckStatusSingleProcess(ModuleParameter)
						if not ProcessIsRunning:
							self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- Process PID " + str(pid) + " has been successfyully killed with signal 9")

					except:
						self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: " + ModuleParameter.ModuleBinary + " -- kill 9 on PID " + str(pid) + " did not succeed: Process seems not to be running, we make it sure by ps command")
						ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)
						pass

				## We probably already called this funtion.. but
				## not really necessarey.. but we go here to make it really sure that the process is really dead
				else:
					ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)

		## the normal Script stuff
		elif ModuleParameter.ModuleStopScript:
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Execute: " + ModuleParameter.ModuleStopScript + " " + ModuleParameter.ModuleStopScriptParameter)
			subprocess.call([ModuleParameter.ModuleStopScript, ModuleParameter.ModuleStopScriptParameter], stdout=subprocess.DEVNULL)
			## we assume, the external script works
			ProcessIsRunning = False
	
		return ProcessIsRunning

	############################################################################################################
	## gets the simple feetback from the starting script calles with the command status
	def CheckStatusSingleProcessByScript(self, ModuleStatusScript, ModuleStatusScriptParameter):
		ProcessIsRunning = False

		try: 
			if ModuleStatusScript:
				#print ("Want to execute : " + ModuleStatusScript + " " + ModuleStatusScriptParameter)
				RetVal = subprocess.check_call([ModuleStatusScript, ModuleStatusScriptParameter], stdout=subprocess.DEVNULL)
				if RetVal == 0:
					ProcessIsRunning = True

		except:
			pass
			
		return ProcessIsRunning

	############################################################################################################
	## do a kill 0 on the PID 
	def CheckStatusSingleProcessByPIDFile(self, ModuleParameter):
		## gets the PID from the PIDFile
		## runs a kill 0 on it, to check if it is running
		
		bRunningStatus = False
		pid = None

		if not os.path.exists(ModuleParameter.ModulePIDFile):
			self.ObjmultusdTools.logger.debug("CheckStatusSingleProcessByPIDFile: PID File for Binary: " + ModuleParameter.ModuleBinary + " not existant we clean up the processes")

			bRunningStatus = self.__StopProcessByPS__(ModuleParameter, bRunningStatus)

			## this here works, but we stop the process it theer should be a PID and there is none instead
			"""
			#print ("CheckStatusSingleProcessByPIDFile: PID File for Binary: " + ModuleParameter.ModuleBinary + " not existant we look in the process list")
			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			Len = len(PIDList)
			if Len and PIDList[0]:
				#print ("CheckStatusSingleProcessByPIDFile: We got " + str(Len) + " processes of binary " + ModuleParameter.ModuleBinary + " running with PIDs: " + str(PIDList))
				## it should run only once, we run a test on the first process
				PsPID = None
				try:
					PsPID = int(PIDList[0])
					os.kill(PsPID, 0)
					bRunningStatus = True
				except:

					self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " CheckStatusSingleProcessByPIDFile: kill 0 on PID " + str(PsPID) + " from ps failed somehow.. it ran into an OS Error")
					## 2021-02-04
					## we make it sure
					bRunningStatus = self.__StopProcessByPS__(ModuleParameter, bRunningStatus)
					pass
			"""
		else:
			try:
				pid = None
				with open(ModuleParameter.ModulePIDFile, "r") as f:
					pid = int(f.read().strip())
					if pid:
						os.kill(pid, 0)
						bRunningStatus = True
			except:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " CheckStatusSingleProcessByPIDFile: PID File exists (PID: " + str(pid) + ") but Process Check with kill 0 failed.. process is not running")
				## 2021-02-04
				## we make it sure
				bRunningStatus = self.__StopProcessByPS__(ModuleParameter, bRunningStatus)
				pass
		return bRunningStatus 

	
	############################################################################################################
	##
	## checks, whether to run a script or a kill -0 on the PID from the pIDFile
	##
	def CheckStatusSingleProcess(self, ModuleParameter):
		ProcessIsRunning = False
		
		#print ("Entered CheckStatusSingleProcess ModuleParameter.ModuleStatusByPIDFileEnable: " + str(ModuleParameter.ModuleStatusByPIDFileEnable))
	
		if ModuleParameter.ModuleStatusByPIDFileEnable:
			ProcessIsRunning = self.CheckStatusSingleProcessByPIDFile(ModuleParameter)
		elif ModuleParameter.ModuleStatusScript:
			ProcessIsRunning = self.CheckStatusSingleProcessByScript(ModuleParameter.ModuleStatusScript, ModuleParameter.ModuleStatusScriptParameter)
		elif ModuleParameter.ModuleBinary and ModuleParameter.ModuleBinaryStartupDirectlyEnable:
			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			if len(PIDList) and len(PIDList[0]):	
				ProcessIsRunning = True

		return ProcessIsRunning 

	############################################################################################################
	##
	## runs a more detailled procedure checking the process
	##
	def __CheckSingleProcess__(self, ModuleCheckScript):
		
		RetVal = True

		if ModuleCheckScript:
			#print ("__CheckSingleProcess__: Executing: " + ModuleCheckScript)
			RV = subprocess.call([ModuleCheckScript], stdout=subprocess.DEVNULL)
			if RV == 0:
				RetVal = True
			else:
				RetVal = False

		return RetVal

