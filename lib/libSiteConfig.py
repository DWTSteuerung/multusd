# -*- coding: utf-8 -*-
#
# Karl Keusgen
# 2020-09-26
#
# Class, that keeps General stuff
#
import os
import sys
import configparser
from email.mime.text import MIMEText
import smtplib

sys.path.append('/multus/lib')
## do the Periodic Alive Stuff
import multusdBasicConfigfileStuff

# 2020-06-01
# Json config option
import libUseJsonConfig
UseJsonConfig = libUseJsonConfig.UseJsonConfig
if UseJsonConfig:
	import urllib.request
	import json

class SiteConfigClass(multusdBasicConfigfileStuff.ClassBasicConfigfileStuff):
	def __init__(self, ObjmultusdTools, ConfigFile = None):
		self.ObjmultusdTools = ObjmultusdTools
		## initialize the parent class
		multusdBasicConfigfileStuff.ClassBasicConfigfileStuff.__init__(self)

		self.ConfigFile = ConfigFile
		self.SoftwareVersion = "1"
	
		return

	def ReadConfig(self):
		bSuccess = False
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden == True:
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')
			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))
			self.SiteName = self.__assignStr__(config.get('SiteName', 'Value'))
			self.SMTPTSLEnable = self.__assignBool__(config.get('SMTPTSLEnable', 'Value'))
			self.SMTPServer = self.__assignStr__(config.get('SMTPServer', 'Value'))
			self.SMTPUser = self.__assignStr__(config.get('SMTPUser', 'Value'))
			self.SMTPPass = self.__assignStr__(config.get('SMTPPass', 'Value'))
			self.SMTPMessageSubject = self.__assignStr__(config.get('SMTPMessageSubject', 'Value'))
			self.SMTPSender = self.__assignStr__(config.get('SMTPSender', 'Value'))
			self.TMailenable = self.__assignBool__(config.get('TMailenable', 'Value'))
			self.CheckDBEnable = self.__assignBool__(config.get('CheckDBEnable', 'Value'))
			self.TMail = self.__assignStr__(config.get('TMail', 'Value'))
			"""
			self.dbservertype = self.__assignStr__(config.get('dbservertype', 'Value'))
			self.servername = self.__assignStr__(config.get('servername', 'Value'))
			self.dbusername = self.__assignStr__(config.get('dbusername', 'Value'))
			self.dbpassword = self.__assignStr__(config.get('dbpassword', 'Value'))
			self.dbRootPassword = self.__assignStr__(config.get('dbRootPassword', 'Value'))
			self.dbname = self.__assignStr__(config.get('dbname', 'Value'))
			self.mysql_opts = { 
			'host': self.servername, 
			'user': self.dbusername, 
			'pass': self.dbpassword, 
			'db': self.dbname
			} 

			self.mysqlRoot_opts = { 
			'host': self.servername, 
			'user': 'root',
			'pass': self.dbRootPassword, 
			'db': self.dbname
			}
			"""
			bSuccess = True
		else:

			print ("No config file .. exiting")

		print ("We read in the site config parameters")
		
		return bSuccess

	# 2020-06-01	
	def ReadJsonConfig(self, ObjmultusdJsonConfig, Ident, Instance = 0):
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
			if self.ObjmultusdTools:
				ErrorString = self.ObjmultusdTools.FormatException()
				LogString = "Read in Json Process config failed with Error: " + ErrorString
				print(LogString)
			
		return bSuccess

	def GetSiteConfigFileAndReadConfig(self, ObjmultusdConfig, AllModules, UseJsonConfig):
		## Now we try to get the database and mail params
		bSuccess = False
		Ident = "Site"
		for Module in AllModules:
			#print ("Searching for our config: Checking module Ident: " + Module.ModuleParameter.ModuleIdentifier + " against our own Ident: " + Ident)
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				print ("GetConfigFileAndReadConfig YYYYYY Got Site Config it")
				if UseJsonConfig:
					bSuccess = self.ReadJsonConfig(ObjmultusdConfig, Ident)
				else:
					self.ConfigFile = Module.ModuleParameter.ModuleConfig
					bSuccess = self.ReadConfig()

		if not bSuccess:
			print ("Error getting Json config")

		return bSuccess
	
	def CheckAndRepairDatabase(self):
		if self.CheckDBEnable:
			self.ObjmultusdTools.logger.debug("Going to check mysql database: " + self.dbname + " on server: " + self.servername)
			mysqlCon, cursor = self.ObjmultusdTools.OpenMySQL(self.mysqlRoot_opts)
			Sql = "show tables"
			cursor.execute(Sql)
			Tables = list()
			rowTables = cursor.fetchone()
			while rowTables:
				Tables.append(rowTables[0])
				rowTables = cursor.fetchone()
			
			TablesToRepair = list()
			for Table in Tables:
				print ("We found table: " + Table)
				Sql = "check table " + Table
				cursor.execute(Sql)
				StatusTable = cursor.fetchone()
				if StatusTable[3] != "OK":
					self.ObjmultusdTools.logger.debug("Error on table: " + Table)
					TablesToRepair.append(Table)
				else:
					self.ObjmultusdTools.logger.debug("Table: " + Table + " is OK")
					
			if len(TablesToRepair):
				MailText = ""
				for Table in TablesToRepair:
					MailText += "Going to repair Table: " + Table + "\n"
					self.ObjmultusdTools.logger.debug("Going to repair Table: " + Table)
					Sql = "repair table " + Table
					cursor.execute(Sql)
					
				self.SendTechnicalInfoEmail("Repaired database on " + self.SiteName , MailText)
					
			self.ObjmultusdTools.CloseMySQL(mysqlCon, cursor)
		return

	def SendTechnicalInfoEmail(self, MailSubject, MailContent):
		if self.TMailenable:
			self.SendEmail(self.TMail, MailSubject, MailContent)
		return

	def SendEmail(self, CSListOfMailReceivers, MailSubject, MailContent):

		try:
			#2017-02-23
			# Überprüfen, ob wir einen NachrichtenInhalt haben
			MailContent = MailContent.strip()

			MailSubject = MailSubject.strip()

			print ("Commaseperated List of Email Receivers: " + str(CSListOfMailReceivers))

			CSListOfMailReceivers = CSListOfMailReceivers.replace(" ", "")
			
			if len(MailContent) and len(CSListOfMailReceivers) and len(MailSubject):	

				ArrayOfMailReceivers = CSListOfMailReceivers.split(",")

				# generate a RFC 2822 message
				MailMessage = MIMEText(MailContent)
				MailMessage['From'] = self.SMTPSender
				MailMessage['To'] = CSListOfMailReceivers
				MailMessage['Subject'] = MailSubject
			
				# open SMTP connection
				LinkToSMTPServer = smtplib.SMTP(self.SMTPServer)
			
				# start TLS encryption
				if self.SMTPTSLEnable:
					print ("We connect secure using TLS")
					LinkToSMTPServer.starttls()
				else:
					print ("We're using an insecure connection")
			
				# login with specified account
				if self.SMTPUser and self.SMTPPass:
					LinkToSMTPServer.login(str(self.SMTPUser), str(self.SMTPPass))
			
				# send generated message
				LinkToSMTPServer.sendmail(self.SMTPSender, ArrayOfMailReceivers, MailMessage.as_string())
			
				# close SMTP connection
				LinkToSMTPServer.quit()
				self.ObjmultusdTools.logger.debug("Successfully send an email to " + str(CSListOfMailReceivers) + " with the subject: " + MailSubject)
		except: 
			if self.ObjmultusdTools:
				ErrorString = self.ObjmultusdTools.FormatException()
				self.ObjmultusdTools.logger.debug("Failed sending an Email with Error: " + ErrorString)

		return

