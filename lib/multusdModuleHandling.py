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

		## In case we got dead processes.. startup of a new one is not allowed..
		## We have to wait, till the old process vanishes from the process list
		self.NoStartupAllowedProcessIsInStrangeState = False

		## delay in process supervising loop
		## standard and maximum value
		self.SleepingTime = 1.0
		return

	############################################################################################################
	def PrepareUpdateDirectory(self, multusdTMPDirectory, ModuleIdentifier):
		self.UpdateDirectory = multusdTMPDirectory + "/" + ModuleIdentifier

		if os.path.exists(self.UpdateDirectory):
			## starting up.. old stuff is not from interest then
			shutil.rmtree(self.UpdateDirectory,  ignore_errors = True)

		os.mkdir(self.UpdateDirectory)
		os.chmod(self.UpdateDirectory,stat.S_IRWXU |stat.S_IRWXG | stat.S_IRWXO)

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
	def __RunPeriodicJob__(self, Module):

		"""
		if self.NoStartupAllowedProcessIsInStrangeState:
			print ("Process is in strange state: " + str(self.NoStartupAllowedProcessIsInStrangeState))
		"""

		# Starting a process
		if (not self.Module.ControlThread or (self.Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and not self.NoStartupAllowedProcessIsInStrangeState and self.StartProcess and not self.ProcessIsRunning and not self.ReloadProcess and not self.StopProcess:
			## first we check, if the process is already running
			self.ProcessIsRunning = self.CheckStatusSingleProcess(Module.ModuleParameter)

			if not self.ProcessIsRunning:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 1 Run a process start procedure for Binary: " + Module.ModuleParameter.ModuleBinary)
				self.__DoJobBeforeStarting__()
				self.StartSingleProcess(Module.ModuleParameter)

				## Check on the success of the starting procedure
				self.ProcessIsRunning = self.CheckStatusSingleProcess(Module.ModuleParameter)

			if self.ProcessIsRunning:
				self.__DoJobAfterStarting__()
				Module.ProcessLastTimeStarted = time.time()
			else:
				## The process or whatever has to be killed...
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 1 Run a process start procedure Binary: " + Module.ModuleParameter.ModuleBinary + " Failed.. process seems not to be running.. we kill it again")
				self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)
		# stopping a process
		elif (not self.Module.ControlThread or (self.Module.ControlThread and not Module.ControlThread.bTimeout)) and self.StopProcess:
			self.StartProcess = False
			self.ReloadProcess = False

			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 2 Run a process stop procedure")
			
			self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)
			self.__DoJobAfterStopping__()

			self.StopProcess = False

			time.sleep (1.0)

			## Check on the success of the stopping procedure

		# restarting a process
		elif (not self.Module.ControlThread or (self.Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and not self.NoStartupAllowedProcessIsInStrangeState and self.ReloadProcess and self.StartProcess:
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 5 Run a process restart procedure " + Module.ModuleParameter.ModuleBinary)

			self.__DoJobBeforeReStarting__()
			self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)
			self.__DoJobAfterStopping__()

			self.StartSingleProcess(Module.ModuleParameter)
			
			## Check on the success of the starting procedure
			self.ProcessIsRunning = self.CheckStatusSingleProcess(Module.ModuleParameter)
			if self.ProcessIsRunning:
				self.ReloadProcess = False
				self.__DoJobAfterStarting__()
				Module.ProcessLastTimeStarted = time.time()
			else:
				## The process or whatever has to be killed...
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " 5 Run a process restart Failed.. we kill process again " + Module.ModuleParameter.ModuleBinary)
				self.ProcessIsRunning = self.StopSingleProcess(Module.ModuleParameter, self.ProcessIsRunning)

		# Periodic Check by script, if there is one
		elif (not self.Module.ControlThread or (self.Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and Module.ModuleParameter.ModulePeriodicCheckEnabled and (self.NextCheckToDo < time.time()):
			print ("Thread: " + self.ThreadName + " 6 Want to run a process check procedure and get the status by a script.. if there is one")
			self.ProcessCheckSucceeded = self.__CheckSingleProcess__(Module.ModuleParameter.ModuleCheckScript)
			self.NextCheckToDo = time.time() + Module.ModuleParameter.ModulePeriodicCheckInterval
			if not self.ProcessCheckSucceeded:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Error: CHecking Module " + Module.ModuleParameter.ModuleIdentifier + " Failure is not running well.. we force a restart")
				self.ReloadProcess = True
				
			# In the End, after the CHecking Process was done, we check the status
			self.ProcessIsRunning = self.CheckStatusSingleProcessByScript(Module.ModuleParameter.ModuleStatusScript, Module.ModuleParameter.ModuleStatusScriptParameter)
		## the Status Check by PID from PIDFile is done independently, if a regular Check is also done
		# periodic check against the PID kill 0
		if (not self.Module.ControlThread or (self.Module.ControlThread and not Module.ControlThread.bTimeout)) and not self.Shutdown and Module.ModuleParameter.ModuleStatusByPIDFileEnable and (self.NextPIDStatusToDo < time.time()):
			#print ("Want to run ")
			# In the End, after the CHecking Process was done, we check the status
			self.ProcessIsRunning = self.CheckStatusSingleProcessByPIDFile(Module.ModuleParameter)
			self.NextPIDStatusToDo = time.time() + Module.ModuleParameter.ModuleStatusByPIDFilePeriod

		return

	############################################################################################################
	def StartSingleProcess(self, ModuleParameter):
		
		if ModuleParameter.ModuleBinaryStartupDirectlyEnable:
			Binary = ModuleParameter.ModuleBinaryPath + "/" + ModuleParameter.ModuleBinary
			print ("StartSingleProcess: Executing: " + Binary + " Parameter: " + ModuleParameter.ModuleBinaryParameter)
			subprocess.call([Binary, ModuleParameter.ModuleBinaryParameter])
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Starting Process Executing: " + Binary + " " + ModuleParameter.ModuleBinaryParameter)
			## We wait for Process to come up and write the PIDFile, otherwise the check if it is runing will fail
			time.sleep(1.0)

			print ("XXXXXXXXXXXXXXXXXXXXXXX Direct startup succeeded") 
			
		elif ModuleParameter.ModuleStartScript:
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StartSingleProcess: Executing: " + ModuleParameter.ModuleStartScript + " " + ModuleParameter.ModuleStartScriptParameter)
			subprocess.call([ModuleParameter.ModuleStartScript, ModuleParameter.ModuleStartScriptParameter])

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
					self.NoStartupAllowedProcessIsInStrangeState = False
				except:
					self.NoStartupAllowedProcessIsInStrangeState = True
					pass
			
			time.sleep(2)
			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			Len = len(PIDList)
			if Len and PIDList[0]:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " We still got several processes of binary " + ModuleParameter.ModuleBinary + " running with PIDs: " + str(PIDList) + " kill them with 9")
				for PID in PIDList:
					try:
						os.kill(int(PID), 9)
						self.NoStartupAllowedProcessIsInStrangeState = False
					except:
						self.NoStartupAllowedProcessIsInStrangeState = True
						pass

			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			Len = len(PIDList)
			if Len and not PIDList[0]:
				ProcessIsRunning = False
				self.NoStartupAllowedProcessIsInStrangeState = False
		else:
			ProcessIsRunning = False
			self.NoStartupAllowedProcessIsInStrangeState = False

		return

	############################################################################################################
	def StopSingleProcess(self, ModuleParameter, ProcessIsRunning):
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
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + "StopSingleProcess: PID File not existant Process does not seem to run we look at the process list via ps command")
				ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)
			else:

				try:
					with open(ModuleParameter.ModulePIDFile, "r") as f:
						pid = int(f.read().strip())
						os.kill(pid, 15)
					
					time.sleep (1.0)
					ProcessIsRunning = EvalProcessIsRunnig(ModuleParameter)

				except:
					self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + "StopSingleProcess: kill 15 on PID " + str(pid) + " did not succeed: Process seems not to be running we go for it via ps comamnd")
					ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)
					time.sleep (1.0)
					pass
			
			# 2020-06-01
			while TimeToFinish > time.time() and ProcessIsRunning:
				ProcessIsRunning = EvalProcessIsRunnig(ModuleParameter)
									
			## Now we make it real sure, that the process is gone
			if not ProcessIsRunning:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: Process PID " + str(pid) + " has been successfyully killed with signal 15")
			else:
				self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + "StopSingleProcess: Process PID " + str(pid) + " is still running we kill em finally with 9")
		
				try:
					os.kill(pid, 9)
					time.sleep(1)

					## We killed the process, now we check if it is still running
					ProcessIsRunning = self.CheckStatusSingleProcessByPIDFile(ModuleParameter)
					if not ProcessIsRunning:
						self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " StopSingleProcess: Process PID " + str(pid) + " has been successfyully killed with signal 9")

				except:
					self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + "StopSingleProcess: kill 9 on PID " + str(pid) + " did not succeed: Process seems not to be running, we make it sure by ps command")
					ProcessIsRunning = self.__StopProcessByPS__(ModuleParameter, ProcessIsRunning)
					pass


		## the normal Script stuff
		elif ModuleParameter.ModuleStopScript:
			self.ObjmultusdTools.logger.debug("Thread: " + self.ThreadName + " Execute: " + ModuleParameter.ModuleStopScript + " " + ModuleParameter.ModuleStopScriptParameter)
			subprocess.call([ModuleParameter.ModuleStopScript, ModuleParameter.ModuleStopScriptParameter])
			## we assume, the external script works
			ProcessIsRunning = False
	
		return ProcessIsRunning

	############################################################################################################

	############################################################################################################
	## gets the simple feetback from the starting script calles with the command status
	def CheckStatusSingleProcessByScript(self, ModuleStatusScript, ModuleStatusScriptParameter):
		ProcessIsRunning = False

		try: 
			if ModuleStatusScript:
				print ("Want to execute : " + ModuleStatusScript + " " + ModuleStatusScriptParameter)
				RetVal = subprocess.check_call([ModuleStatusScript, ModuleStatusScriptParameter])
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
			print ("CheckStatusSingleProcessByPIDFile: PID File for Binary: " + ModuleParameter.ModuleBinary + " not existant we look in the process list")

			PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
			Len = len(PIDList)
			if Len and PIDList[0]:
				print ("CheckStatusSingleProcessByPIDFile: We got " + str(Len) + " processes of binary " + ModuleParameter.ModuleBinary + " running with PIDs: " + str(PIDList))
				## it should run only once, we run a test on the first process
				try:
					os.kill(int(PIDList[0]), 0)
					bRunningStatus = True
				except:

					self.NoStartupAllowedProcessIsInStrangeState = True
					print ("CheckStatusSingleProcessByPIDFile: kill 0 on PID from ps failed somehow.. it ran into an OS Error")
					pass
			else:
				self.NoStartupAllowedProcessIsInStrangeState = False
		else:
			try:
				with open(ModuleParameter.ModulePIDFile, "r") as f:
					pid = int(f.read().strip())
					if pid:
						os.kill(pid, 0)
						bRunningStatus = True
						self.NoStartupAllowedProcessIsInStrangeState = False
			except:
				print ("CheckStatusSingleProcessByPIDFile: PID File exists but Process Check with kill 0 failed.. process is not running")
				## We look on strange processes in ps
				PIDList = self.__CheckOnProcessInPS__(ModuleParameter.ModuleBinary)
				Len = len(PIDList)
				if Len and PIDList[0]:
					self.NoStartupAllowedProcessIsInStrangeState = True
				else:
					self.NoStartupAllowedProcessIsInStrangeState = False

				pass

		return bRunningStatus 

	############################################################################################################
	##
	## checks, whether to run a script or a kill -0 on the PID from the pIDFile
	##
	def CheckStatusSingleProcess(self, ModuleParameter):
		RetVal = False
		
		#print ("Entered CheckStatusSingleProcess ModuleParameter.ModuleStatusByPIDFileEnable: " + str(ModuleParameter.ModuleStatusByPIDFileEnable))
	
		if ModuleParameter.ModuleStatusByPIDFileEnable:
			RetVal = self.CheckStatusSingleProcessByPIDFile(ModuleParameter)
		else:
			RetVal = self.CheckStatusSingleProcessByScript(ModuleParameter.ModuleStatusScript, ModuleParameter.ModuleStatusScriptParameter)

		return RetVal

	############################################################################################################
	##
	## runs a more detailled procedure checking the process
	##
	def __CheckSingleProcess__(self, ModuleCheckScript):
		
		RetVal = True

		if ModuleCheckScript:
			print ("__CheckSingleProcess__: Executing: " + ModuleCheckScript)
			RV = subprocess.call([ModuleCheckScript])
			if RV == 0:
				RetVal = True
			else:
				RetVal = False

		return RetVal

