# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2019-11-16
# Extension of the old multus hardware class, which came with the multus thrift server
# this extened class is to be used in native multusd environment
#
#

import time
import sys
import RPi.GPIO as GPIO

sys.path.append('/multus/lib')
import DWTThriftmultus3

class multusHardwareHandlerClass(DWTThriftmultus3.DWTRaspIOHandler):
	
	def __init__(self, multusModbusConfig, multusdToolsInstance):
		DWTThriftmultus3.DWTRaspIOHandler.__init__(self, multusModbusConfig, multusdToolsInstance)

		self.multusModbusConfig = multusModbusConfig
		self.ReadDOStatus = list()

		self.bInitResetRS485rBNKTermination = False
		self.bInitResetrBNK = False

		self.adc = None
		return


	def __del__(self):

		return

	## 2020-10-05
	def InitDOSet(self):
		DOSet = list()
		i = 0
		LenHardwareOutputs = len(self.Config.multusHardware.DOCH)
		print ("We are going to int the DOSet .. Number of configured Digital Outputs: " + str(LenHardwareOutputs))
		while i < LenHardwareOutputs:
			DOSet.append(-1)
			i += 1

		return DOSet

	## 2020-10-27
	## fix old typO
	def WriteDO(self, address, ios):
		return self.writeDO(address, ios)

	def InitReadDOStatus(self):
		if self.multusModbusConfig.MySQLEnable:
			self.ThriftMySQL.InitLastReadDOValues()
		i = 0
		while i < len(self.Config.multusHardware.DOCH):
			#print ("Call ReadStatusOfDO with index: " + str(i))
			self.ReadDOStatus.append(self.ReadStatusOfDos(i, True))

			i = i + 1

		print ("Initializing of RadDO Status finished.. current DO Status: " + str(self.ReadDOStatus))	
		return

	## OK.. old stuff reads one input out... don't knoww..
	def ReadStatusOfDos(self, DOField, bInit = False):
		### in the DOAdresses are all available DO Systems
		#print (str(self.Config.multusHardware.DOAdresses))
		#print (str(self.Config.multusHardware.DOCH))

		#print ("bInit: " + str(bInit))
	
		ReturnValue = None

		if DOField >= 0 and DOField < len(self.Config.multusHardware.DOCH):
			ReturnValue = GPIO.input(self.Config.multusHardware.DOCH[DOField])

		if not bInit and self.Config.MySQLEnable and self.Config.MySQLThriftLoggingEnable:
			print ("assign DOField " + str(DOField) + " with value: " + str(ReturnValue))
			self.ReadDOStatus[DOField] = ReturnValue
			self.ThriftMySQL.LogReadDOEvent(self.ReadDOStatus)
		
		return ReturnValue 


	##
	## 2021-02-11
	def ReadStatusOfAllDos(self):

		i = 0
		while i < len(self.Config.multusHardware.DOCH):
			#print ("Call ReadStatusOfDO with index: " + str(i))
			status = self.ReadStatusOfDos(i)
			if status == 0:
				self.ReadDOStatus[i] = 1
			else:
				self.ReadDOStatus[i] = 0

			i = i + 1
		
		return self.ReadDOStatus


	# 2020-01-22
	def EnableHWWatchdog(self):
		## First initialize the 2 needed outputs as output
		GPIO.setup(self.Config.multusHardware.GpioWDSet, GPIO.OUT)
		GPIO.setup(self.Config.multusHardware.GpioWDWDI, GPIO.OUT)
		print ("Enable HW-Watchdog on GPIO: " + str(self.Config.multusHardware.GpioWDSet))
		GPIO.output(self.Config.multusHardware.GpioWDSet, GPIO.HIGH)

		self.TriggerHWWatchdog()
		pass

	def DisableHWWatchdog(self):
		print ("Disable HW-Watchdog on GPIO: " + str(self.Config.multusHardware.GpioWDSet))
		GPIO.output(self.Config.multusHardware.GpioWDSet, GPIO.LOW)
		GPIO.output(self.Config.multusHardware.GpioWDWDI, GPIO.LOW)
		pass

	def TriggerHWWatchdog(self):
		#print ("Trigger HW-Watchdog on GPIO: " + str(self.Config.multusHardware.GpioWDWDI) + " Timestamp: " + str(time.time()))
		GPIO.output(self.Config.multusHardware.GpioWDWDI, GPIO.HIGH)
		time.sleep (0.01)
		GPIO.output(self.Config.multusHardware.GpioWDWDI, GPIO.LOW)
		pass

	def HandleRS485rBNKTermination(self, bEnableTermination = True):
		if not self.bInitResetRS485rBNKTermination:
			GPIO.setup(self.Config.multusHardware.GpioRS485rBNKTermination, GPIO.OUT)
			self.bInitResetRS485rBNKTermination = True

		if bEnableTermination:
			GPIO.output(self.Config.multusHardware.GpioRS485rBNKTermination, GPIO.HIGH)

			self.Tools.logger.debug("Set RS485 termination of rBNK communication line (GPIO: " + str(self.Config.multusHardware.GpioRS485rBNKTermination) + ")")
		else:
			GPIO.output(self.Config.multusHardware.GpioRS485rBNKTermination, GPIO.LOW)
			self.Tools.logger.debug("UnSet RS485 termination of rBNK communication line.. line not terminated now")

	def ResetrBNK(self):
		if not self.bInitResetrBNK:
			GPIO.setup(self.Config.multusHardware.GpiorBNKReset, GPIO.OUT)
			self.bInitResetrBNK = True

		GPIO.output(self.Config.multusHardware.GpiorBNKReset, GPIO.HIGH)
		time.sleep (0.5)
		GPIO.output(self.Config.multusHardware.GpiorBNKReset, GPIO.LOW)
		self.Tools.logger.debug("Done reset of rBNK device")

	############################################################################################################
	## 2021-02-09
	##
	## python3 update of ReadAI
	##
	def InitMCP3208(self):
		import mcp3208

		self.adc = mcp3208.MCP3208()

	def	ReadAI3 (self, address):
		volts = None
		if not self.adc:
			self.Tools.logger.debug("ReadAI3 Funktion not initialized.. run InitMCP3208() first")
		else:	
			self.Tools.logger.debug("ReadAI3 Funktion entered, opening CS: " + str(self.Config.multusHardware.AIAdresses[address]))

			AI = list()
			volts = list()
		
			MaxAnalogInputs = 5
			i = 0
			while i < MaxAnalogInputs:
				AI.append(self.adc.read(i))
				volts.append(AI[-1] * (10.0/4095.0))
				i += 1

			self.Tools.logger.debug("ReadAI3: ch0=%5.3f V,  ch1=%5.3f V,  ch2=%5.3f V,  ch3=%5.3f V,  ch4=%5.3f V" % (volts[0], volts[1], volts[2], volts[3], volts[4]))

		return volts

