# -*- coding: utf-8 -*-
# Karl Keusgen
# 2019-05-03
#
# port to python3 on 2019-10-24
#

import logging
import logging.handlers
#import MySQLdb
# 2019-09-03
#from logging import Logger

import pymysql
import sys
import linecache
import time
import random
import hashlib
import os
import stat

class DWTThriftToolsClass(object):

	class ThriftUserLoginClass:
		def __init__(self):
			self.UserName = ""
			self.UserHandle = 0
			self.LoginCreated = 0
			self.LoginLatestActivity = 0

	############################################################################################################
	def __init__(self):

		self.UserHandlesLogin = list()
		self.logger = None

		print ("initializing DWTThriftTools Class")
		

	############################################################################################################
	def __del__(self):
		print ("exiting ToolsClass")

	############################################################################################################
	### 2019-05-01 ###
	def OpenMySQL(self, mysql_opts):
		
		#print ("Mysql Host: " + mysql_opts['host'] + " User: " +mysql_opts['user'] + " Pass: " +mysql_opts['pass'] + " DB: " + mysql_opts['db'])

		#mysqlCon = MySQLdb.connect(mysql_opts['host'], mysql_opts['user'], mysql_opts['pass'], mysql_opts['db']) 
		mysqlCon = pymysql.connect(mysql_opts['host'], mysql_opts['user'], mysql_opts['pass'], mysql_opts['db']) 
		mysqlCon.apilevel = "2.0" 
		mysqlCon.threadsafety = 2 
		mysqlCon.paramstyle = "format"
		cursor = mysqlCon.cursor()

		return mysqlCon, cursor
		
	############################################################################################################
	def CloseMySQL(self, mysqlCon, cursor):
		cursor.close ()
		mysqlCon.close ()	
		return

	############################################################################################################
	### 2019-05-01 ###
	### Auch das Logging wir an verschiedenen Stellen benoetigt.. 
	###
	### Mit dem Aufruf dieser Funktion auch mit verschiedenen LogFile Namen kann nur eine Instanz initialisiert werden
	def InitLogging(self, LogFile):

		lhandler = logging.handlers.WatchedFileHandler(LogFile)
		logger = logging.getLogger(__name__)
		## Normal loggin to StdOut
		logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
		formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
		lhandler.setFormatter(formatter)
		lhandler.setLevel(logging.DEBUG)
		#Adding handler to logger
		logger.addHandler(lhandler)

		print ("Loggin Initialisiere Hardware Log")
				
		return logger

	############################################################################################################
	### 2019-05-01 ###
	### fuer das globale logging nutzen wir einen logger handler in der tools Klasse
	def InitGlobalLogging(self, LogFile):
		self.logger = self.InitLogging(LogFile)

		# 2021-02-08
		# set the file permissions right
		bLogFileExists = os.path.exists(LogFile)
		print ("InitGlobalLogging: LogFIle: " + LogFile + " os.exists: " + str(bLogFileExists))

		if not bLogFileExists:
			self.logger.debug("DWTThriftToolsClass:InitGlobalLogging: Logging initialized")
	
		os.chmod(LogFile, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)

		return

	## 2019-05-09
	def FormatException(self):
		exc_type, exc_obj, tb = sys.exc_info()
		f = tb.tb_frame
		lineno = tb.tb_lineno
		filename = f.f_code.co_filename
		linecache.checkcache(filename)
		line = linecache.getline(filename, lineno, f.f_globals)
		ErrorString = 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)
		
		return ErrorString

	############################################################################################################
	############################################################################################################
	### 2019-05-12 ###
	### The whole DWTThift User Handling stuff
	def ThriftUserCheckUserAlreadyPresent(self, UserName):
		#print ("Entered check User already present")
		i = 0
		for User in self.UserHandlesLogin:
			#print ("CheckUserAlredyPresent: " + User.UserName)
			if UserName == User.UserName:
				return True, User.UserHandle, i
			i = i + 1

		return False, 0, 0

	############################################################################################################
	def ThriftUserCheckValidUserHandle(self, UserHandle):
		PresentIndex = 0
		for User in self.UserHandlesLogin:
			if UserHandle == User.UserHandle:
				## bei dieser Gelegenheit aktualisierenw ir gleich den ActivitY Timestamp
				self.UserHandlesLogin[PresentIndex].LoginLatestActivity = time.time()
				return True, User.UserName

			PresentIndex = PresentIndex + 1

		return False, ""

	############################################################################################################
	def ThriftUserCheckExpiredLogins(self, Config):
		ListToBeDeleted = list()
		i = 0
		j = 0

		strUserDoDelete = ""

		for User in self.UserHandlesLogin:
			if (User.LoginLatestActivity + Config.ThriftLoginExpires) < time.time():
				if len(strUserDoDelete):
					strUserDoDelete = strUserDoDelete + ", " + User.UserName 
				else:
					strUserDoDelete = User.UserName 
				ListToBeDeleted.append(i)
				j = j + 1
			
			i = i + 1
		
		while j > 0:
			j = j - 1
			del self.UserHandlesLogin[ListToBeDeleted[j]]

		ListToBeDeleted[:]
		return strUserDoDelete

	############################################################################################################
	def ThriftUserLogin (self, Config, UserName, PassWord):
		PresentIndex = 0
		bUserAlreadyPresent = False
		UserHandle = 0

		## zuerst mal pruefen, ob es ueberhaupt ein zugelassener Nutzer ist
		#print ("Versuchter LOgin von: " + UserName + ":" + PassWord)
		bUserFound = False
		for User in Config.ThriftUsersDB:

			#print ("Wir vergleichen jetzt " + User.User + ":" + User.Pass)
			
			if UserName == User.User:
				bUserFound = True
				#Ok, wir habene eine User, wir pruefen jetzt das PAsswort
				EncryptedPass = hashlib.sha1(PassWord.encode())
				#print ("The hexadecimal equivalent of SHA1 is : ")
				#print (EncryptedPass.hexdigest())

				if User.Pass == EncryptedPass.hexdigest():
					## Soweit so gut.. es gibt den User und er hat sich korrekt autehntifiziert
					## Damit wir den gleichen user nicht mehrfach anlegen, pruefen wir, ob er vielelicht schon angemeldet ist
					bUserAlreadyPresent, UserHandle, PresentIndex= self.ThriftUserCheckUserAlreadyPresent(UserName)	
					
					if not bUserAlreadyPresent:
						UserHandle = random.randint(1, 2147483647)

						self.UserHandlesLogin.append(self.ThriftUserLoginClass())
						i = len(self.UserHandlesLogin) - 1
						self.UserHandlesLogin[i].UserName = UserName
						self.UserHandlesLogin[i].UserHandle = UserHandle
						self.UserHandlesLogin[i].LoginCreated = time.time()
						self.UserHandlesLogin[i].LoginLatestActivity = time.time()

						print ("User " + UserName + " logged in successfully User Position in List: " + str(i))
					
					else:
						## Wir update den Zeitstempel	
						self.UserHandlesLogin[PresentIndex].LoginLatestActivity = time.time()
				else:
					print ("Failed login of User " + UserName + " Wrong Password")

				## Wir haben den User gefunden.. dann brauchen wir nicht weiter zu suchen
				break

		if not bUserFound:
			print ("Failed login of User " + UserName + " invalid UserName")

		return UserHandle

	############################################################################################################
	def ThriftUserLogout(self, UserHandle):
		strUserName = ""
		ListToBeDeleted = list()
		i = 0
		j = 0

		for User in self.UserHandlesLogin:
			if User.UserHandle == UserHandle:
				if len(strUserName):
					strUserName = strUserName + ", " + User.UserName
				else:
					strUserName = User.UserName
				ListToBeDeleted.append(i)
				j = j + 1
			
			i = i + 1

		while j > 0:
			j = j - 1
			del self.UserHandlesLogin[ListToBeDeleted[j]]

		ListToBeDeleted[:]
		return strUserName 

