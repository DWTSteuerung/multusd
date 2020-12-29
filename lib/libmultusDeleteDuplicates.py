# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2020-12-28
#
import os
import sys
import time
import configparser
import hashlib

sys.path.append('/multus/lib')
## do the Periodic Alive Stuff
import multusdControlSocketClient
import DWTThriftConfig3

# 2020-06-01
# Json config option
import libUseJsonConfig
UseJsonConfig = libUseJsonConfig.UseJsonConfig
import urllib.request
import json

############################################################################################################
#
# 2019-12-07
# Class to be called by multusdService
# it is mandatory for each native multusd process, who uses the controlPort function
# to have a class like this
#
class FailSafeClass(object):
	def __init__(self, Tools, ModuleConfig, Ident, dBNKEnabled):
		
		self.Ident = Ident
		
		return

	def SetIntoFailSafeState(self, ProcessIsRunning):

		return

	def ExecuteAfterStop(self, ProcessIsRunning):

		return

	def ExecuteAfterStart(self, ProcessIsRunning):

		return

	def ExecutePeriodic(self, ProcessIsRunning):

		return
############################################################################################################

class multusDeleteDuplicatesConfigClass(DWTThriftConfig3.ConfigDataClass):
	def __init__(self, ConfigFile):
		## initialize the parent class
		DWTThriftConfig3.ConfigDataClass.__init__(self)

		self.ConfigFile = ConfigFile
		self.SoftwareVersion = "1"
	
		return

	def ReadConfig(self):
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden == True:
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')
			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))
			self.SearchForDuplicatesEnable = self.__assignBool__(config.get('SearchForDuplicatesEnable', 'Value'))
			self.DeleteDuplicatesEnable = self.__assignBool__(config.get('DeleteDuplicatesEnable', 'Value'))
			self.PathToCheck = self.__assignStr__(config.get('PathToCheck', 'Value'))
			self.RunOnlyOnceEnable = self.__assignBool__(config.get('RunOnlyOnceEnable', 'Value'))
			self.IntervalToCheck = self.__assignInt__(config.get('IntervalToCheck', 'Value'))
			self.ThriftMysqlOpts = self.__ReadMySQLParameter__(self.ConfigFile)
			## BasicPath Index
			self.Index_BP = None

		else:

			print ("No config file .. exiting")
			return False

		print ("multusDeleteDuplicates started with these parameters")
		print ("multusDeleteDuplicates : " + str(self.ConfigVersion))

		return True

	# 2020-06-01	
	def ReadJsonConfig(self, ObjmultusdTools, ObjmultusdJsonConfig, Ident, Instance = 0):
		bSuccess = False
		try: 
			Timeout = 5
			url = ObjmultusdJsonConfig.JsonSingleModuleURL + Ident
			print ("We get the Json process config form url: " + url)
			with urllib.request.urlopen(url , timeout = Timeout) as url:
				ConfigData = json.loads(url.read().decode())

			#print (ConfigData)
			for (ModuleKey, ModuleValue) in ConfigData.items():
				if ModuleKey == "Instances":
					# We walk through the instaces looking for the required one	
					InstanceCounter = 0
					for SingleInstance in ModuleValue:
						if InstanceCounter == Instance:
							print ("We found the parameters of this process: " + str(SingleInstance))
							self.ConfigVersion = SingleInstance['ConfigVersion']
							self.DummyParam = SingleInstance['DummyParam']
							break

						InstanceCounter += 1

			bSuccess = True
		except:
			ErrorString = ObjmultusdTools.FormatException()
			LogString = "Read in Json Process config failed with Error: " + ErrorString
			print(LogString)
			
		return bSuccess

############################################################################################################

class multusDeleteDuplicatesOperateClass(object):
	def __init__(self, ObjmultusDeleteDuplicatesConfig, ObjmultusdTools):

		self.ObjmultusDeleteDuplicatesConfig = ObjmultusDeleteDuplicatesConfig
		self.ObjmultusdTools = ObjmultusdTools
		
		#Setup mysql Connection
		self.mysqlCon, self.cursor = self.ObjmultusdTools.OpenMySQL(self.ObjmultusDeleteDuplicatesConfig.ThriftMysqlOpts)
		self.KeepThreadRunning = True
		
		return

############################################################
	def __del__(self):
		print ("leaving multusDeleteDuplicatesOperateClass")
		pass

############################################################
	def WalkThroughDirectories(self):

		# SubFunction
		def FileAsBytes(file):
			with file:
				return file.read()

		# MainFunction
		for ExtendedPath, dirs, files in os.walk("."):
			self.DoPeriodicMessage()

			if ExtendedPath and len(files):
				Index_EP = None
				## check EP_Path on existance
				while not Index_EP:
					SQL="select INDEX_EP from ExtendedPath where EP_Path='"+ ExtendedPath + "' and EP_Index_BP=" + str(self.ObjmultusDeleteDuplicatesConfig.Index_BP)
					self.cursor.execute(SQL)
					data=self.cursor.fetchone()

					if data:
						Index_EP = data[0]
						print ("We got Index of path " + ExtendedPath + ": " + str(Index_EP)) 
					else:
						print("we did not find the path: " + ExtendedPath +  " in the database")	
						SQL="insert into ExtendedPath set EP_Path='" + ExtendedPath + "', EP_Index_BP=" + str(self.ObjmultusDeleteDuplicatesConfig.Index_BP) + ", EP_TSCreated=sysdate()"
						self.cursor.execute(SQL)

				#not from interest... 
				"""
				for Directory in dirs:
					print("Directory: " + Directory)
				"""

				for FileName in files:
					self.DoPeriodicMessage()

					Index_FI = None
					while not Index_FI:
						SQL="select INDEX_FI, FI_MD5Sum from Files where FI_FileName='"+ FileName + "' and FI_Index_EP=" + str(Index_EP) + " and FI_Deleted = '0'"
						self.cursor.execute(SQL)
						data=self.cursor.fetchone()

						if data:
							Index_FI = data[0]
							## build md5 Fingeprint compare and update on demand
							MD5Fingerprint = hashlib.md5(FileAsBytes(open(os.path.join(ExtendedPath, FileName), 'rb'))).hexdigest()
							print ("We got Index of Filename " + FileName + ": " + str(Index_FI) + " Actual Fingerprint is: " + MD5Fingerprint) 
							if not data[1] or MD5Fingerprint != data[1]:
								print ("Update MD5 Fingerprint in Database")
								SQL = "update Files set FI_MD5Sum='" + MD5Fingerprint + "', FI_TSChanged=sysdate() where INDEX_FI=" + str(Index_FI)
								self.cursor.execute(SQL)
							else:
								print ("MD5 Fingerprint unchanged")
						else:
							print("we did not find the Filename: " + FileName +  " in the database")	
							SQL="insert into Files set FI_FileName='" + FileName + "', FI_Index_EP=" + str(Index_EP) + ", FI_TSCreated=sysdate()"
							self.cursor.execute(SQL)

					#print("Filename: " + FileName + " Joined: " + os.path.join(ExtendedPath, FileName))
					if not self.KeepThreadRunning:
						break

			if not self.KeepThreadRunning:
				break
		return

############################################################
	def CheckFilesOnDuplicates(self):
		SQL = "select INDEX_FI, FI_MD5Sum, FI_DoubleIndex from ExtendedPath, Files where FI_Deleted = '0' and INDEX_EP = FI_Index_EP and EP_Index_BP=" + str(self.ObjmultusDeleteDuplicatesConfig.Index_BP)
 
		self.cursor.execute(SQL)
		rows = self.cursor.fetchall()
		MaxElements = len(rows)
		
		for i in range(0, MaxElements -1):
			self.DoPeriodicMessage()
		
			for k in range(i + 1, MaxElements - 1):
				self.DoPeriodicMessage()
				if rows[i][1] == rows[k][1]:
					self.DoPeriodicMessage()
					print ("Found double file to Index_FI: " + str(rows[i][0]) + " Index " + str(rows[k][0]) + " is the same file")
					SQL = "update Files set FI_DoubleIndex=" + str(rows[i][0]) + " where INDEX_FI=" + str(rows[k][0])
					self.cursor.execute(SQL)
					break

				if not self.KeepThreadRunning:
					break

			if not self.KeepThreadRunning:
				break
				
		return

############################################################
	def DeleteDuplicates(self):
		SQL = "select INDEX_FI, EP_Path, FI_FileName, FI_DoubleIndex from ExtendedPath, Files where FI_DoubleIndex != 0 and FI_Deleted = '0'and INDEX_EP = FI_Index_EP and EP_Index_BP=" + str(self.ObjmultusDeleteDuplicatesConfig.Index_BP)
		self.cursor.execute(SQL)
		rows = self.cursor.fetchall()

		for row in rows:
			self.DoPeriodicMessage()

			DuplicateToDelete = os.path.join(row[1], row[2])
			print ("We intend to delete File: " + DuplicateToDelete )
			try:
				os.remove(DuplicateToDelete)
				SQL = "update Files set FI_Deleted='1', FI_TSDeleted=sysdate() where INDEX_FI=" + str(row[0])
				self.cursor.execute(SQL)
			except:
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("Error deleting File: " + DuplicateToDelete + ": " + ErrorString)

			if not self.KeepThreadRunning:
				break
		return

############################################################
	## TODO function not perfect.. will not work on a line of empty directories... so it has to be called multiple times
	def DeleteEmptyDirectories(self):
		DeletedAtLeastOneDirectory = False
		for ExtendedPath, dirs, files in os.walk("."):
			self.DoPeriodicMessage()

			if ExtendedPath and not len(files) and not len(dirs) and ExtendedPath != ".":
				self.ObjmultusdTools.logger.debug("We found empty directory: " + ExtendedPath + " we are going to delete")
				os.rmdir(ExtendedPath)
				DeletedAtLeastOneDirectory = True

		return DeletedAtLeastOneDirectory

############################################################
	def DoPeriodicMessage(self):
		if self.periodic:
			Timestamp = time.time()
			if Timestamp >= self.TimestampNextmultusdPing:
				self.periodic.SendPeriodicMessage()
				self.TimestampNextmultusdPing = time.time() + self.multusdPingInterval
				
			if self.periodic.WeAreOnError:
				self.ObjmultusdTools.logger.debug("Error connecting to multusd... we stop running")
				self.KeepThreadRunning = False
		return 

############################################################
	def Operate(self, multusdPingInterval, bPeriodicEnable, ModuleControlPort):
		self.multusdPingInterval = multusdPingInterval
		## setup the periodic alive mnessage stuff
		self.periodic = None
		if bPeriodicEnable:
			print ("Setup the periodic Alive messages")
			self.TimestampNextmultusdPing = time.time()
			self.periodic = multusdControlSocketClient.ClassControlSocketClient(self.ObjmultusdTools, 'localhost', ModuleControlPort)
			if not self.periodic.ConnectFeedbackSocket():
				self.ObjmultusdTools.logger.debug("Stopping Process, cannot establish Feedback Connection to multusd")
				sys.exit(1)

		# 2020-01-01
		# the loop shall not sleep longer than 1 second.. otherwise the handling in the stop procedure gets too slow
		SleepingTime = self.multusdPingInterval
		if self.multusdPingInterval > 1.0:
			SleepingTime = 1.0

		## We get the Index of the path in the database"
		NextPathCheck = time.time()
		while not self.ObjmultusDeleteDuplicatesConfig.Index_BP:
			SQL="select INDEX_BP from BasicPath where BP_Path='"+ self.ObjmultusDeleteDuplicatesConfig.PathToCheck + "'"
			self.cursor.execute(SQL)
			data=self.cursor.fetchone()

			if data:
				self.ObjmultusDeleteDuplicatesConfig.Index_BP = data[0]
				self.ObjmultusdTools.logger.debug("We got Index of path " + self.ObjmultusDeleteDuplicatesConfig.PathToCheck + ": " + str(self.ObjmultusDeleteDuplicatesConfig.Index_BP)) 
			else:
				self.ObjmultusdTools.logger.debug("we did not find the path: " + self.ObjmultusDeleteDuplicatesConfig.PathToCheck +  " in the database")	
				SQL="insert into BasicPath set BP_Path='"+ self.ObjmultusDeleteDuplicatesConfig.PathToCheck + "', BP_TSCreated=sysdate()"
				self.cursor.execute(SQL)
			
		DoNotRunTwice = False

		# main loop
		while self.KeepThreadRunning:
			
			Timestamp = time.time()
			self.DoPeriodicMessage()

			# get the current path
			SavedPath = os.getcwd()
			## first we change to the path
			os.chdir(self.ObjmultusDeleteDuplicatesConfig.PathToCheck)

			if not DoNotRunTwice and (self.ObjmultusDeleteDuplicatesConfig.DeleteDuplicatesEnable or self.ObjmultusDeleteDuplicatesConfig.SearchForDuplicatesEnable) and NextPathCheck < Timestamp:
				if self.ObjmultusDeleteDuplicatesConfig.SearchForDuplicatesEnable:
					self.ObjmultusdTools.logger.debug("Start performing check on duplicates in Path: " + self.ObjmultusDeleteDuplicatesConfig.PathToCheck)

					# do the check
					self.WalkThroughDirectories()

					## OK, now we got all MD5 fingeprints in the database.. we are going to compare the files...
					self.CheckFilesOnDuplicates()
					
					self.ObjmultusdTools.logger.debug("Finished check on duplicates in Path: " + self.ObjmultusDeleteDuplicatesConfig.PathToCheck + " operation took: " + str(int(time.time() - Timestamp)) + " seconds")

				if self.KeepThreadRunning and self.ObjmultusDeleteDuplicatesConfig.DeleteDuplicatesEnable:
					Timestamp2 = time.time()
					self.ObjmultusdTools.logger.debug("Start deleting duplicates in Path: " + self.ObjmultusDeleteDuplicatesConfig.PathToCheck)
					self.DeleteDuplicates()
					DeletedAtLeastOneDirectory = True
					while DeletedAtLeastOneDirectory:
						print ("Call DeleteEmptyDirectories()")

						DeletedAtLeastOneDirectory = self.DeleteEmptyDirectories()

					self.ObjmultusdTools.logger.debug("Finished deletion of duplicates in Path: " + self.ObjmultusDeleteDuplicatesConfig.PathToCheck + " operation took: " + str(int(time.time() - Timestamp2)) + " seconds")

				if self.ObjmultusDeleteDuplicatesConfig.RunOnlyOnceEnable:
					self.ObjmultusdTools.logger.debug("We will not run for a second time")
					DoNotRunTwice = True

				NextPathCheck = time.time() + float(self.ObjmultusDeleteDuplicatesConfig.IntervalToCheck) 

			time.sleep (SleepingTime)

		# change back
		os.chdir(SavedPath)

		return
