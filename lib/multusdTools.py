#
# Karl Keusgen
# 2019-11-02
#
# several utilities needed all the time
#
#

import os
import sys
import stat
import pprint
import ipaddress

sys.path.append('/multus/lib')
import DWTThriftTools3

class multusdToolsClass(DWTThriftTools3.DWTThriftToolsClass):
	
	def __init__(self):
		DWTThriftTools3.DWTThriftToolsClass.__init__(self)
		
		# create the temp directory path
		self.multusdTMPDirectory = "/multus/tmp"
		self.ControlPortThreadSuffix = "Control"
		self.multusdServiceThreadSuffix = "multusdService"

		return

	# 2020-02-16
	def GetInterfaceIP(self, Interface = 'tunbnk'):
		IP = None
		try:
			# 2020-01-25 identify the system bu the IP of then tunbnk interface
			f = os.popen("/sbin/ip -4 address show dev " + Interface + " | /bin/grep inet | /bin/grep -v inet6 | /usr/bin/awk '{print $2}'")
			IPInterim = f.read().replace('\n','')
			## Check on valid IP Adress format
			Values = IPInterim.split('.')
			if len(Values) == 4:
				IPInvalid = False
				for Val in Values:
					nVal = int(Val)
					if nVal < 0 or nVal > 255:
						IPInvalid = True

				if not IPInvalid:
					IP = IPInterim
					#pprint.pprint ("IP native: " + IP) 
					if self.logger:
						self.logger.debug("Got IP of interface: " + Interface + " : " + IP)
					else:
						print("Got IP of interface: " + Interface + " : " + IP)

		except:
			ErrorString = self.FormatException()
			IP = None
			ErrorString = self.FormatException()
			if self.logger:
				self.logger.debug("Fatal ERROR occured getting IP of interface: " + Interface + " : " + ErrorString)
			else:
				print("Fatal ERROR occured getting IP of interface: " + Interface + " : " + ErrorString)

		if not self.AdressIsValidIPv4Address(IP): 
			IP = None
			if self.logger:
				self.logger.debug("ERROR Got an illegal IP on interface " + Interface + " IP: " + str(IP))
			else:
				print("ERROR Got an illegal IP on interface " + Interface + " IP: " + str(IP))


		return IP
	
	## 2020-03-22
	## the automatic type conversion by python is not too reliable... .. it took me 24hrs....
	def ExtractValueFromgRPCRequest(self, gRPCRequest, VariableName, DataType):
		def DoConversion(DType, DStrValue):
		## We found the variable.. now we do the typecast
			if DType == 'float':
				if not len(DStrValue) or not DStrValue.replace('.','').isnumeric():
					DValue = 0.0
				else:
					DValue = float(DStrValue)
			elif DType == 'int':
				if not len(DStrValue) or not DStrValue.isnumeric():
					DValue = 0
				else:
					DValue = int(DStrValue)
			elif DType == 'long':
				if not len(DStrValue) or not DStrValue.isnumeric():
					DValue = 0
				else:
					DValue = long(DStrValue)
			elif DType == 'bool':
				if not len(DStrValue):
					DValue = False
				else:
					DValue = bool(DStrValue)
			elif DType == 'str':
				#pprint.pprint(DStrValue)
				DValue = DStrValue
				#pprint.pprint(DValue.replace('\n',''))
			elif DType == 'bytes':
				DValue = bytes(DStrValue)

			return DValue

		Value = None
		NotFound = True
		#print ("ExtractValueFromgRPCRequest: We got this gRPC Request thing:")
		
		#pprint.pprint(str(gRPCRequest))
		SplitByNewline = str(gRPCRequest).split('\n')

		for Element in SplitByNewline:
			SE = Element.split(':')
			if len(SE) >= 2:
				StrVariable = str(SE[0].strip())
				StrValue = str(SE[1].strip())
				if StrVariable == VariableName:
					NotFound = False
					Value = DoConversion(DataType, StrValue)	
		if NotFound:
			Value = DoConversion(DataType, '')	

		return Value
			
	# 2020-08-10
	def AdressIsValidIPv4Address(self, address):
		bSuccess = True
		try:
			ipaddress.ip_address(address)
			bAddressLenRight = address.count('.') == 3
		except:
			bSuccess = False

		return bSuccess and bAddressLenRight
