# -*- coding: utf-8 -*-
#
# Karl Keusgen
#
# 2019-11-16
# Modbus Server for the multus hardware providing 0x04, 0x05, 0x06 functionaltity
#

import logging
import socketserver
import umodbus
import umodbus.server.tcp
import umodbus.utils
import sys

import threading

import os
import configparser
sys.path.append('/multus/lib')
import DWTThriftConfig3

UseJsonConfig = False
############################################################################################################
#
# 2019-12-07
# Class to be called by multusdService
# it is mandatory for each native multusd process, who uses the controlPort function
# to have a class like this
#
class FailSafeClass(object):
	def __init__(self, Tools, ModuleConfig, Ident, DSVIntegrityEnabled):
		
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


class ModbusConfigClass(DWTThriftConfig3.ConfigDataClass):
	def __init__(self, ConfigFile):
		self.ConfigFile = ConfigFile
		DWTThriftConfig3.ConfigDataClass.__init__(self)

		self.ThriftMysqlOpts = None
		self.MySQLThriftLoggingEnable = False
		self.MySQLRestoreDOEnable = False

		# 2021-02-07
		self.SoftwareVersion = "1"
		
		self.ModuleControlPortEnabled = True
		self.ModuleControlFileEnabled = False
		self.ModuleControlPort = 43000

		return

	def ReadConfig(self):
		# config fuer die zu nutzenden Dateien
		ConfVorhanden = os.path.isfile(self.ConfigFile)

		if ConfVorhanden:
			
			config = configparser.ConfigParser()
			config.read(self.ConfigFile, encoding='utf-8')
			self.SoftwareVersion = "1.0.0"
			self.ConfigVersion = self.__assignStr__(config.get('ConfigVersion', 'Value'))
			self.ModbusPort = self.__assignInt__(config.get('ModbusPort', 'Value'))
			self.ModbusTCPBindIP = self.__assignStr__(config.get('ModbusTCPBindIP', 'Value'))
			self.ModbusSlaveID = self.__assignInt__(config.get('ModbusSlaveID', 'Value'))
			self.ModbusReadOnly = self.__assignBool__(config.get('ModbusReadOnly', 'Value'))
			self.InputRegisterStart = self.__assignInt__(config.get('InputRegisterStart', 'Value'))
			self.CountInputRegisters = self.__assignInt__(config.get('CountInputRegisters', 'Value'))
			self.OutputRegisterStart = self.__assignInt__(config.get('OutputRegisterStart', 'Value'))
			self.CountOutputRegisters = self.__assignInt__(config.get('CountOutputRegisters', 'Value'))
			self.StatusOutputRegisters = self.__assignInt__(config.get('StatusOutputRegisters', 'Value'))

			self.MySQLEnable = self.__assignBool__(config.get('MySQLEnable', 'Value'))
			if self.MySQLEnable:
				### Wenn das True ist, dann koennen wir direkt die mysql Zugangs Parameter holen
				self.ThriftMysqlOpts = self.__ReadMySQLParameter__(self.ConfigFile)

				### Und wir schauen, ob wir in die Datenbank auch loggen sollen
				self.MySQLThriftLoggingEnable = self.__assignBool__(config.get('MySQLThriftLoggingEnable', 'Value'))

				self.MySQLRestoreDOEnable = self.__assignBool__(config.get('MySQLRestoreDOEnable', 'Value'))
		else:

			print ("No config file .. exiting")
			return False

		print ("multusModbus started with these parameters")
		print ("multusModbus Port: " + str(self.ModbusPort))
		print ("multusModbus BindIP: " + str(self.ModbusTCPBindIP))
		print ("multusModbus SlaveID: " + str(self.ModbusSlaveID))
		print ("multusModbus ReadOnly: " + str(self.ModbusReadOnly))
		print ("multusModbus Input Register start: " + str(self.InputRegisterStart))
		print ("multusModbus Count Input Registers: " + str(self.CountInputRegisters))
		print ("multusModbus Output registers start: " + str(self.OutputRegisterStart))
		print ("multusModbus Count Output Registers: " + str(self.CountOutputRegisters))
		print ("multusModbus Status Output Registers, what has been set on the outputs: " + str(self.StatusOutputRegisters))
		
		return True


class multusModbusHandlerThread(threading.Thread):
	def __init__(self, ObjModbusConfig, ObjmultusdTools, ObjmultusHardware):

		self.ThreadName = "ModbusHandler"
		super(multusModbusHandlerThread, self).__init__(name = self.ThreadName)

		self.ObjmultusHardware = ObjmultusHardware
		self.ObjmultusdTools = ObjmultusdTools
		self.ObjModbusConfig = ObjModbusConfig

		self.KeepThreadRunning = True

		return

	def StartmultusModbusServer(self):

		# Add stream handler to logger 'uModbus'.
		#umodbus.utils.log_to_stream(level=logging.DEBUG)
		umodbus.utils.log_to_stream(level=logging.CRITICAL)

		umodbus.conf.SIGNED_VALUES = False

		self.ObjmultusdTools.logger.debug("Starting Modbus TCP Listening Server on IP: " + str(self.ObjModbusConfig.ModbusTCPBindIP) + " Listening on Port: " + str(self.ObjModbusConfig.ModbusPort))

		socketserver.TCPServer.allow_reuse_address = True
		self.ObjumodbusServer = umodbus.server.tcp.get_server(socketserver.TCPServer, (self.ObjModbusConfig.ModbusTCPBindIP, self.ObjModbusConfig.ModbusPort), umodbus.server.tcp.RequestHandler)
		self.ObjumodbusServer._shutdown_request = False

		FirstInputRegister = self.ObjModbusConfig.InputRegisterStart
		LastInputRegister = self.ObjModbusConfig.InputRegisterStart + (self.ObjModbusConfig.CountInputRegisters)

		############################################################################################################
		@self.ObjumodbusServer.route(slave_ids=[self.ObjModbusConfig.ModbusSlaveID], function_codes=[3, 4], addresses=list(range(FirstInputRegister, LastInputRegister)))
		def read_data_store3_4(slave_id, function_code, address):
			print ("Call function read_data_store3_4 Address: " + str(address) + " FunctionCode: " + str(function_code) + " SlaveID = " + str(slave_id))
			
			## TODO this can be optimized... but then the old database Log-Function has to be updated
			print ("We read in all Digital Inputs at once")
			DIStatus = self.ObjmultusHardware.readDI(0)
			
			Field = address - FirstInputRegister
			if Field >= 0 and Field <= len(DIStatus):
				ReturnValue = DIStatus[address - FirstInputRegister] == 0
			else:
				ReturnValue = None

			return ReturnValue
	
		############################################################################################################
		if not self.ObjModbusConfig.ModbusReadOnly:
			FirstOutputRegister = self.ObjModbusConfig.OutputRegisterStart
			LastOutputRegister = self.ObjModbusConfig.OutputRegisterStart + (self.ObjModbusConfig.CountOutputRegisters)

			@self.ObjumodbusServer.route(slave_ids=[self.ObjModbusConfig.ModbusSlaveID], function_codes=[5, 15], addresses=list(range(FirstOutputRegister, LastOutputRegister)))
			def write_data_store6_16(slave_id, function_code, address, value):
				print ("write_data_store6_16 slave_id: " + str(slave_id) + " Function Code: " + str(function_code) + " Adress: " + str(address) + " value: " + str(value))

				#if function_code == 16 and (address == 10 or address == 11):
				DOSet = list()
				i = 0
				while i < self.ObjModbusConfig.CountOutputRegisters:
					DOSet.append(-1)
					i = i + 1

				DOSet[address - FirstOutputRegister] = int(value) == 0
				
				self.ObjmultusHardware.writeDO(0, DOSet)
				
				return

		FirstStatusOutputRegister = self.ObjModbusConfig.StatusOutputRegisters
		LastStatusOutputRegister = self.ObjModbusConfig.StatusOutputRegisters + (self.ObjModbusConfig.CountOutputRegisters)
############################################################################################################
		@self.ObjumodbusServer.route(slave_ids=[self.ObjModbusConfig.ModbusSlaveID], function_codes=[3, 4], addresses=list(range(FirstStatusOutputRegister, LastStatusOutputRegister)))
		def read_data_store3_4(slave_id, function_code, address):
			print ("Call function read_data_store3_4 Address: " + str(address) + " FunctionCode: " + str(function_code) + " SlaveID = " + str(slave_id))
			
			DOField = address - FirstStatusOutputRegister
			print ("We read in Status of all Digital Outputs: " + str(DOField))
			ReturnValue = self.ObjmultusHardware.ReadStatusOfDos(DOField) 

			return ReturnValue

		return

	def __del__(self):

		return
	
	def stop():

		return


	def run(self):
		while self.KeepThreadRunning:
			try:
				self.ObjumodbusServer.serve_forever()
			finally:
				self.ObjumodbusServer.shutdown()
				self.ObjumodbusServer.server_close()
		return
