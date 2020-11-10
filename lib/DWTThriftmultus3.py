# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# Der gesammte hardware Zugriff, wie er bspw. vom 
# Thrift Server genutzt und dort auch definiert wird
# started as part of DWTThrift server project 2016-02-23
#
# put it into a seperate class
# 2019-04-29
#
# port to python3 on 2019-10-24
#

import sys
import time
import os
from subprocess import Popen , PIPE
import MCP4922
import mcp3208 as MCP3208 

#BPI
#import wiringpi2 as wiringpi
import wiringpi
import RPi.GPIO as GPIO

# 2017-05-19
# wegen restart OpenVPN
from subprocess import call

# 2019-11-03
# integration into multusIII dynamic config files system
sys.path.append('/multus/lib')
import multusdConfig
import multusdModuleConfig
import DWTThriftMySQL3 as DWTThriftMySQL
 
class DWTRaspIOHandler(object):

	############################################################################################################
	def __init__(self, ThriftConfigData, DWTThriftToolsInstance):
		self.Config = ThriftConfigData 
		self.Tools = DWTThriftToolsInstance

		## No ReadDI Entered function logging... 
		self.bReadDIDetailledLogging = False

		# first we get the config of the multusd system
		ObjmultusdConfig = multusdConfig.ConfigDataClass()
		ObjmultusdConfig.readConfig()
	
		## after we got the modules init file.. we have to read it, to get the config files for this process
		multusdModulesConfig = multusdModuleConfig.ClassModuleConfig(ObjmultusdConfig)
		## read separatly
		multusdModulesConfig.ReadModulesConfig()
	
		## First get the hardware config
		## Old hard coded
		#multusHardwareConfH = "/usr/local/etc/multus/php/multusHardware.conf" 
		
		#WalkThe list of modules to find our configuration files.. 
		Ident = "Hardware"
		for Module in multusdModulesConfig.AllModules:
			#print (str(Module.ModuleParameter.ModuleConfig))
			if Module.ModuleParameter.ModuleIdentifier == Ident:
				multusHardwareConfH = Module.ModuleParameter.ModuleConfig
				break

		self.Config.ReadMultusHardwareConfig(multusHardwareConfH)

		if self.Config.MySQLEnable:
			self.Tools.logger.debug("Rufe MySQL Klasse auf")			
			self.ThriftMySQL = DWTThriftMySQL.ThriftMySQL(self.Config, self.Tools)

			## mal sehen, ob auch das logging enabled wurde
			if self.Config.MySQLThriftLoggingEnable:
				self.ThriftMySQL.InitLastValues()
				
		else:
			self.Tools.logger.debug("MySQL Klasse disabled")			

		# SoC als Pinreferenz waehlen
		GPIO.setmode(GPIO.BCM) 
		GPIO.setwarnings(False)

		# Globale Variable fuer den letzten DO Status
		self.DOStatus = list()
		self.LastDOStatus = [1, 1, 1, 1, 1, 1, 1, 1]

		wiringpi.wiringPiSetupGpio()
		self.__InitInputs__(self.Config.multusHardware.DIAdresses, self.Config.multusHardware.DICH, PUDInit = self.Config.multusHardware.PUDInit)
		self.__InitOutputs__(self.Config.multusHardware.DOAdresses, self.Config.multusHardware.DOCH)
	
		self.Tools.logger.debug("Thrift Server multus Hardware Access Class started")

	############################################################################################################
	def __del__(self):
		self.Tools.logger.debug("Thrift Server multus Hardware Access Class Finished")
		
	############################################################################################################
	def __InitOutputs__(self, DOAdresses, LocalDOCH):
		# Digital Out
		# Altes Board bis version .2 Verwendet als Ausgang GPIOs
		# Ab Version .3 wird ein PCF8574 Verwendet
		# RPi.GPIO Layout verwenden

		self.Tools.logger.debug("Initialiere Outputs")

		AnzahlAusgangsModule=len(DOAdresses)

		j=0

		while j < AnzahlAusgangsModule:

			#print "Ausgang: ", j
			if DOAdresses[j] == 0:

				### 2019-05-02
				#### Falls wir das MySQL Logging enabled haben
				#### koennen wir den letzten DO Status fuer die
				#### bank 0 aus der Datenbank holen
				if self.Config.MySQLEnable and self.Config.MySQLThriftLoggingEnable:
					self.Tools.logger.debug("Wir lesen den alten DO Status aus der Datenbank")
					self.LastDOStatus = self.ThriftMySQL.ReadLastDOMySQL(DOAdresses[j])

				# Native GPIOS
				AnzahlDO = len(LocalDOCH)
				i=0
				while i < AnzahlDO:
					GPIO.setup(LocalDOCH[i], GPIO.OUT)

					## Wenn wir den alten Wert haben, dann setzen wir ihn auch
					if self.Config.MySQLRestoreDOEnable and self.Config.MySQLEnable and self.Config.MySQLThriftLoggingEnable:
						if self.LastDOStatus[i] == 0:
							self.Tools.logger.debug("Wir setzen DO "  + str(i + 1) + " High")
							GPIO.output(LocalDOCH[i], GPIO.HIGH)
						else:
							self.Tools.logger.debug("Wir setzen DO "  + str(i + 1) + " Low")
							GPIO.output(LocalDOCH[i], GPIO.LOW)

					i=i+1
			else:
				DOBasePin = 100 + (8 * (DOAdresses[j] - 0x38))
				Pin=0

				# I2C GPIOS
				wiringpi.pcf8574Setup(DOBasePin,DOAdresses[j])

				# Immer 8 Ausgaenge pro Adresse
				k=0
				while k < 8:
					# GPIO Pins setzen
					wiringpi.pinMode(DOBasePin + Pin, 1)
					wiringpi.digitalWrite(DOBasePin + Pin, 1)
					Pin = Pin + 1
					k = k+1

			### Wir initialisieren den DOStatus
			self.DOStatus.append(self.LastDOStatus)

			j=j+1

		return

	############################################################################################################
	def __InitInputs__(self, DIAdresses, LocalDICH, PUDInit = 0):

		self.Tools.logger.debug("Initialiere Inputs")

		## 2020-05-21
		## The standard is no Pull up or pull down
		if PUDInit == 0:
			self.Tools.logger.debug("Inputs: Disable Pull Up/Down resistors")
			EffectivePUDInit = GPIO.PUD_OFF
		elif PUDInit > 0:
			self.Tools.logger.debug("Inputs: Enable Pull-Up resistors")
			EffectivePUDInit = GPIO.PUD_UP
		elif PUDInit < 0:
			self.Tools.logger.debug("Inputs: Enable Pull-Down resistors")
			EffectivePUDInit = GPIO.PUD_DOWN
		else:
			self.Tools.logger.debug("Inputs: Error nothing specified according Pull Up/Down resistors")
			

		AnzahlInputModule = len(DIAdresses)
		j=0
		while j < AnzahlInputModule:
			
			#print "Eingang: ", j

			if DIAdresses[j] == 0:
				# Pin DI1 als Input setzen
				AnzahlDI = len(LocalDICH)
				i=0
				while i < AnzahlDI:
					GPIO.setup(LocalDICH[i], GPIO.IN, pull_up_down = EffectivePUDInit)  
					i=i+1
			else:
				#print DIAdresses[j]
				DIBasePin = 200 + (8 * (DIAdresses[j] - 0x38))
				Pin=0

				# I2C GPIOS
				wiringpi.pcf8574Setup(DIBasePin, DIAdresses[j])

				# Immer 8 Ausgaenge pro Adresse
				k=0
				while k < len(self.Config.multusHardware.DOCH):
					# GPIO Pins als Input setzen
					wiringpi.pinMode(DIBasePin + Pin, 0)
					Pin = Pin + 1
					k = k+1

			j = j+1

		return

	############################################################################################################
	def RaspIOPing(self):
		self.Tools.logger.debug("RaspIOPing()")
		return 1

	############################################################################################################
	def RestartOpenVPN(self):
		self.Tools.logger.debug("RestartOpenVPN()")
		#call ("/etc/init.d/openvpn", "restart")
		os.system("/usr/local/thrift/DWTRaspIO/py-impl/restart-openvpn.py")
		return 0

	############################################################################################################
	def writeDO (self, address, ios):
		#self.Tools.logger.debug("WriteDO()")
		#self.Tools.logger.debug(str(ios))

		AnzahlAusgangsModule=len(self.Config.multusHardware.DOAdresses)

		# nachschauen of es dieses Ausgangsmodul geben kann
		if address < AnzahlAusgangsModule:
			#print ("Wir setzen DO  Modul mit Adresse: " + str(self.Config.multusHardware.DOAdresses[address]))
			## 2018-05-01 das ist ein bisschen zu einfach
			## auf diese weise kann der Status -1 einen alten gueltigen Status ueberschreiben
			##self.DOStatus[address] = ios

			AnzahlElementeA = len(self.DOStatus[address])
			AnzahlElementeN = len(ios)

			i = 0

			while i < AnzahlElementeA and i < AnzahlElementeN:
				if ios[i] == 0 or ios[i] == 1:
					self.DOStatus[address][i] = ios[i]

				i = i + 1
		else:
			self.Tools.logger.debug("WriteDO() ungueltiges Ausgangsmodul Nr: " + str(address))
				
		AnzahlElemente=len(ios)

		i=0
		
		if self.Config.multusHardware.DOAdresses[address] == 0:
			#print ("Hallo Standard DO")
			# Adresse 0: native GPIOs
			while i < AnzahlElemente:
				if ios[i] == 0:
					GPIO.output(self.Config.multusHardware.DOCH[i], GPIO.HIGH)
				elif ios[i] > 0:
					# keusgen 2016-07-13 Wenn Wert kleiner als 0, dann lassen wir den Ausgang wie er ist
					# bei 1 setzen wir ihn auf 0
					GPIO.output(self.Config.multusHardware.DOCH[i], GPIO.LOW)

				#print i
				i = i + 1
			
			### 2019-04-30
			if self.Config.MySQLEnable and self.Config.MySQLThriftLoggingEnable:
				self.ThriftMySQL.LogDOEvent(ios)

		else:
			# I2c GPIOS
			DOBasePin = 100 + (8 * (self.Config.multusHardware.DOAdresses[address] - 0x38))
			while i < AnzahlElemente:
			
				if ios[i] == 0:
					wiringpi.digitalWrite(DOBasePin + (7-i), 0)

				elif ios[i] > 0:
					# keusgen 2016-07-13 Wenn Wert kleiner als 0, dann lassen wir den Ausgang wie er ist
					wiringpi.digitalWrite(DOBasePin + (7-i), 1)

				i = i + 1

		return 0

	############################################################################################################
	def	ReadAI (self, address):

		self.Tools.logger.debug("ReadAI Funktion entered, opening CS: " + str(self.Config.multusHardware.AIAdresses[address]))

		MCP3208.open_spi(0, self.Config.multusHardware.AIAdresses[address])

		count = 0
		AI = [0, 0, 0, 0, 0, 0, 0, 0]
		volts = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ]
	
		AI[0] = MCP3208.read(0)
		AI[1] = MCP3208.read(1)
		AI[2] = MCP3208.read(2)
		AI[3] = MCP3208.read(3)
		AI[4] = MCP3208.read(4)
		AI[5] = MCP3208.read(5)
		AI[6] = MCP3208.read(6)
		AI[7] = MCP3208.read(7)

		MCP3208.close_spi()

		# 0 .. 5 normale 0V..10V Eingaenge
		volts[0] = AI[0] * (10.0/4095.0)
		volts[1] = AI[1] * (10.0/4095.0)
		volts[2] = AI[2] * (10.0/4095.0)
		volts[3] = AI[3] * (10.0/4095.0)
		volts[4] = AI[4] * (10.0/4095.0)
		volts[5] = AI[5] * (10.0/4095.0)
		volts[6] = AI[6] * (4.095/4095.0)
		volts[7] = AI[7] * (4.095/4095.0)

		# 6 PT100
		Temp100 = ((103800.0/1589.0) * volts[6]) - (223777.0/7945.0)

		# 7 Stromwandler / Aktivgleichrichter
		# Umrechnung fuer 1A Wandler
		current = (330.0/1193.0) * volts[7] + (87751.0/11930000.0)

		self.Tools.logger.debug("ReadAI: ch0=%5.3f V (%d) ,  ch1=%5.3f V,  ch2=%5.3f V,  ch3=%5.3f V,  ch4=%5.3f V,  ch5=%5.3f V,  (ch6=%5.3f V) Temp=%5.3f C, (ch7 nativ: %5.3f) ch7=%5.3f V RMS" % (volts[0], AI[0], volts[1], volts[2], volts[3], volts[4], volts[5], volts[6], Temp100, volts[7], current))

		print ("ch0=%5.3f V,  ch1=%5.3f V,  ch2=%5.3f V,  ch3=%5.3f V,  ch4=%5.3f V,  ch5=%5.3f V,  (ch6=%5.3f V) Temp=%5.3f C, (ch7 nativ: %5.3f) ch7=%5.3f V RMS" % (volts[0], volts[1], volts[2], volts[3], volts[4], volts[5], volts[6], Temp100, volts[7], current))
	
		return volts

	############################################################################################################
	def readCurrentTransformer(self, address):

		self.Tools.logger.debug("readCurrentTransformer Funktion entered, opening CS: " + str(self.Config.multusHardware.AIAdresses[address]))

		MCP3208.open_spi(0, self.Config.multusHardware.AIAdresses[address])

		count = 0
		AI = [0]
		volts = [0.0]
		current = [0.0]
	
		AI[0] = MCP3208.read(7)

		MCP3208.close_spi()

		# 7 Stromwandler / Aktivgleichrichter
		volts[0] = AI[0] * (4.095/4095.0)
		current[0] = (330.0/1193.0) * volts[0] + (87751.0/11930000.0)

		if current[0] < 0.0:
			current[0] = 0.0

		self.Tools.logger.debug("readCurrentTransformer: ch7 (nativ: %5.3f) ch7=%5.3f A RMS" % (volts[0], current[0]))

		print ("ch7 (nativ: %5.3f) ch7=%5.3f A RMS" % (volts[0], current[0]))
	
		return current


	############################################################################################################
	def readPT100(self, address):
		# TODO im Augenblick geht nur ein Modul
		# TODO CSAI variable richtig auswerten
		self.Tools.logger.debug("ReadPT100 Funktion entered, opening CS: " + str(self.Config.multusHardware.AIAdresses[address]))

		MCP3208.open_spi(0, self.Config.multusHardware.AIAdresses[address])

		count = 0
		AI = [0]
		volts = [ 0.0 ]
		PT100 = [ 0.0 ]
	
		AI[0] = MCP3208.read(6)

		MCP3208.close_spi()

		# 6 PT100
		volts[0] = AI[0] * (4.095/4095.0)
		# 6 PT100
		PT100[0] = ((103800.0/1589.0) * volts[0]) - (223777.0/7945.0)

		self.Tools.logger.debug("ReadPT100:  (ch6=%5.3f V) Temp=%5.3f C " % (volts[0], PT100[0],))
		#logging.debug(time.strftime("%Y-%m-%d %H:%M:%S") + " ReadPT100:  (ch6=%5.3f V) " % (volts[0],))
		#logging.debug(time.strftime("%Y-%m-%d %H:%M:%S") + " ReadPT100:  Temp=%5.3f C " % (PT100[0],))

		print ("(ch6=%5.3f V) Temp=%5.3f C" % (volts[0], PT100[0]))
	
		return PT100 

	############################################################################################################
	def readlastDO(self, address):
		self.Tools.logger.debug("ReadLastDO Funktion entered")

		LastDO = self.DOStatus[address] 
		
		return LastDO

	############################################################################################################
	def readDI(self, address):
		if self.bReadDIDetailledLogging:
			self.Tools.logger.debug("ReadDI Funktion entered")

		DIBasePin = 200 + (8 * (self.Config.multusHardware.DIAdresses[address] - 0x38)) 
		
		DISet = []
		i = 0
		String=""
		# es wird immer ein Satz von 8 Eingaengen gelesen
		while i < len(self.Config.multusHardware.DICH):
			if self.Config.multusHardware.DIAdresses[address] == 0:
				DISet.append (GPIO.input(self.Config.multusHardware.DICH[i]))
			else:
				DISet.append (wiringpi.digitalRead(DIBasePin + i))
				

			String = String + " Kanal " + str(i) + ": " + str(DISet[i])
			i=i+1

		### 2019-04-30
		if self.Config.MySQLEnable and self.Config.MySQLThriftLoggingEnable and self.Config.multusHardware.DIAdresses[address] == 0:
			self.ThriftMySQL.LogDIEvent(DISet)

		if self.bReadDIDetailledLogging:
			self.Tools.logger.debug(String)
		
		return DISet

	############################################################################################################
	def readOnboardLM75(self, address):

		self.Tools.logger.debug("ReadOnboardLM75 Funktion entered")
	
		#SLAVE_ADDR = 0x48
		SLAVE_ADDR = self.Config.multusHardware.LM57Adresses[address]
		# Banana Pi
		p = Popen(['i2cget' , '-y' , str(self.Config.multusHardware.I2CBus), str(SLAVE_ADDR) , '0x00' , 'w'] ,\
	 	stdout=PIPE)
		output = p.stdout.read()

		rawData = int(output , 16)

		degrees = rawData & 0xFF 	#cut high byte off, get low byte000
		degreesAfterDecimal = rawData >> 15	#shift msb to lsb place
 
		if (degrees & 0x80) != 0x80:	  #msb in low byte is 0 -> positive temperature
			temperature = degrees + degreesAfterDecimal * 0.5
		else:	#msb in low byte is 1 -> negative temperature
			#calc two's complement
			degrees = -((~degrees & 0xFF) + 1)
			temperature = degrees + degreesAfterDecimal * 0.5
		
		print ("Current temperature is %s degree celsius" % (str(temperature)))

		return temperature


	############################################################################################################
	def __ma_to_12_bit__(self, val):
		# Wir gehen von einer Spannungsangabe von 0..10V aus...
		# 10V entsprechen Uges
		#12 Bit entsprechen 4095 Stufen
		if val > 10.0:
			val = 10.0
		
		if val < 0.0:
			val = 0.0
		
		NormierteAusgabe = val * float(self.Config.multusHardware.MaxBits)/10.0
		
		return int(NormierteAusgabe)

	############################################################################################################
	def writeAO (self, address, ios):
		self.Tools.logger.debug("WriteAO()")
		self.Tools.logger.debug(str(ios))

		AnzahlElemente=len(ios)

		i=0

		MCP4922.open_spi(0, self.Config.multusHardware.AOAdresses[address])
	
		while i < AnzahlElemente:
			MCP4922.set_value(self.__ma_to_12_bit__(ios[i]), i)
			i = i + 1

		MCP4922.close_spi()

		return 0

