# -*- coding: utf-8 -*-
# Karl Keusgen
# 2019-04-29
#
# port to python3 on 2019-10-24
#
#
# 2019-11-03
## adapted it to multusIII config file format
#

import configparser
import sys

sys.path.append('/multus/lib')
import multusdBasicConfigfileStuff

class ConfigDataClass(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):

	class DWTmultusHardwareStuffClass:
		def __init__(self):
			self.MaxBits = 0
			self.I2CBus=1

			## Alle Adressen werden hex Angegeben
			self.LM57Adresses = list()
			self.AIAdresses = list()
			self.AOAdresses = list()
			self.DOAdresses = list()
			self.DIAdresses = list()

			## Liste der Hardware Raspi Pins
			self.DOCH = list()
			self.DICH = list()
			
			## 2020-05-21
			## Use of processor internal pullups on GPIO input
			self.PUDInit = 0

			## 2920-06-15
			## multus-III hardware controlls
			self.GpioWDSet = 0
			self.GpioWDWDI = 0
			self.GpioFTDIReset = 0
			self.GpioLANRun = 0
			self.GpioUSB2 = 0
			self.GpioUSB3 = 0

	class DWTThriftUsersClass:
		def __init__(self):
			self.UID = 0
			self.User = ""
			self.Pass = ""
			self.UserName = ""
			self.UserEMail = ""

	############################################################################################################
	def __init__(self):
		#self.MySQLConf = MySQLConf
		
		## initialize the parent class
		multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		self.ThriftPort = 9091
		self.LogFile = None

		## old stuff
		self.ThriftUsers = list()
		self.ThriftLoginExpires = 3600

		### 2019-04-30
		### Fuer DB logging und bei Bedarf Thrift User Zugangsdaten
		self.MySQLEnable = False
		self.MySQLThriftLoggingEnable = False
		self.MySQLRestoreDOEnable = False
		self.ThriftMysqlOpts = list ()

		## Harwdare Parameter
		self.multusHardware = self.DWTmultusHardwareStuffClass()

	############################################################################################################
	def __del__(self):
		print ("exiting ConfigClass")

	############################################################################################################
	def __ReadMultusHardwareConf__(self, InitFile):
		
		config = configparser.ConfigParser()
		config.read(InitFile, encoding='utf-8')
		
		print ("Opening InitFile: " + InitFile)
		
		### default Part
		### 2019-05-30 no more defaults..

		### IOs
		self.multusHardware.MaxBits = self.__assignInt__(config.get('Bitrate', 'Value'))
		self.multusHardware.I2CBus = self.__assignInt__(config.get('I2CBus', 'Value'))

		LM57Adresses = self.__assignStr__(config.get('LM75Adresses', 'Value'))
		self.multusHardware.LM57Adresses = [int(item.strip(), 16) for item in LM57Adresses.split(",")]
		AOAdresses = self.__assignStr__(config.get('AOAdresses', 'Value'))
		self.multusHardware.AOAdresses = [int(item.strip(), 16) for item in AOAdresses.split(",")]
		AIAdresses = self.__assignStr__(config.get('AIAdresses', 'Value'))
		self.multusHardware.AIAdresses = [int(item.strip(), 16) for item in AIAdresses.split(",")]

		DOAdresses = self.__assignStr__(config.get('DOAdresses', 'Value'))
		self.multusHardware.DOAdresses = [int(item.strip(), 16) for item in DOAdresses.split(",")]
		DIAdresses = self.__assignStr__(config.get('DIAdresses', 'Value'))
		self.multusHardware.DIAdresses = [int(item.strip(), 16) for item in DIAdresses.split(",")]
		DOCH = self.__assignStr__(config.get('DOCH', 'Value'))
		self.multusHardware.DOCH = [int(item.strip()) for item in DOCH.split(",")]
		DICH = self.__assignStr__(config.get('DICH', 'Value'))
		self.multusHardware.DICH = [int(item.strip()) for item in DICH.split(",")]

		# 2020-05-21
		self.multusHardware.PUDInit = self.__assignInt__(config.get('PUDInit', 'Value'))
		print ("Read in Pull up pull down stuff with value: " + str(self.multusHardware.PUDInit))

		# 2020-06-15
		self.multusHardware.GpioWDSet = self.__assignInt__(config.get('GpioWDSet', 'Value'))
		self.multusHardware.GpioWDWDI = self.__assignInt__(config.get('GpioWDWDI', 'Value'))
		self.multusHardware.GpioFTDIReset = self.__assignInt__(config.get('GpioFTDIReset', 'Value'))
		self.multusHardware.GpioLANRun = self.__assignInt__(config.get('GpioLANRun', 'Value'))
		self.multusHardware.GpioUSB2 = self.__assignInt__(config.get('GpioUSB2', 'Value'))
		self.multusHardware.GpioUSB3 = self.__assignInt__(config.get('GpioUSB3', 'Value'))
		self.multusHardware.GpioRS485rBNKTermination = self.__assignInt__(config.get('GpioRS485rBNKTermination', 'Value'))
		self.multusHardware.GpiorBNKReset = self.__assignInt__(config.get('GpiorBNKReset', 'Value'))

		return 

	############################################################################################################
	def __ReadMySQLParameter__(self, InitFile):
		
		config = configparser.ConfigParser()
		config.read(InitFile, encoding='utf-8')

		dbservertype = self.__assignStr__(config.get('dbservertype', 'Value'))
		servername = self.__assignStr__(config.get('servername', 'Value'))
		dbusername = self.__assignStr__(config.get('dbusername', 'Value')) 
		dbpassword = self.__assignStr__(config.get('dbpassword', 'Value'))
		dbname = self.__assignStr__(config.get('dbname', 'Value'))

		print ("MySQL Daten eingelesen: " + dbservertype)

		return {'host': servername, 'user': dbusername, 'pass': dbpassword, 'db': dbname}

	############################################################################################################
	def ReadMultusHardwareConfig(self, multusHardwareConf):
		#self.mysql_opts = self.__ReadMySQLParameter__(self.MySQLConf)

		self.__ReadMultusHardwareConf__(multusHardwareConf)

		return

	############################################################################################################
	def ReadThriftConfig(self, InitFile, MySQLIniFile):
		config = configparser.ConfigParser()
		config.read(InitFile, encoding='utf-8')
		
		print ("Opening InitFile: " + InitFile)
		
		self.ThriftPort = self.__assignInt__(config.get('ThriftPort', 'Value'))
		self.LogFile = self.__assignStr__(config.get('LogFile', 'Value'))

		self.MySQLEnable = self.__assignBool__(config.get('MySQLEnable', 'Value'))

		if self.MySQLEnable:
			### Wenn das True ist, dann koennen wir direkt die mysql Zugangs Parameter holen
			self.ThriftMysqlOpts = self.__ReadMySQLParameter__(MySQLIniFile)

			### Und wir schauen, ob wir in die Datenbank auch loggen sollen
			self.MySQLThriftLoggingEnable = self.__assignBool__(config.get('MySQLThriftLoggingEnable', 'Value'))

			self.MySQLRestoreDOEnable = self.__assignBool__(config.get('MySQLRestoreDOEnable', 'Value'))
			
			print ("self.MySQLRestoreDOEnable: " + str(self.MySQLRestoreDOEnable))

		return


	############################################################################################################
	def GetDWTThriftUsers(self, ThriftTools):
		mysqlCon, cursor = ThriftTools.OpenMySQL(self.ThriftMysqlOpts)
		Sql = "select INDEX_TU, TU_UserLogin, TU_UserPass, TU_UserName, TU_UserEMail from ThriftUser where TU_Status='1'"
		cursor.execute(Sql)
		data = cursor.fetchall()
		i = 0
		for row in data:
			self.ThriftUsers.append(self.DWTThriftUsersClass())
			self.ThriftUsers[i].UID = row[0]
			self.ThriftUsers[i].User = row[1]
			self.ThriftUsers[i].Pass = row[2]
			self.ThriftUsers[i].UserName = row[3]
			self.ThriftUsers[i].UserEMail = row[4]

			i = i + 1
		
		ThriftTools.CloseMySQL(mysqlCon, cursor)
		return
	
