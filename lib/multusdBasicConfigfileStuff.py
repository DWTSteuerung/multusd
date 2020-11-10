# Karl Keusgen
# 2019-10-31
#
# sharing config files with php may lead into problems..
# lets do the type conversions right
#


class ClassBasicConfigfileStuff(object):
	def __init__(self):
		print ("starting ClassBasicConfigfileStuff")

		return

	############################################################################################################
	def __del__(self):
		print ("exiting ClassBasicConfigStyleStuff")
	
		return

	############################################################################################################
	#
	# handling the Keywords True and False
	# but also 0 and 1
	# 
	#
	def __assignBool__(self, value):
		TrimValue = self.__assignStr__(value)
		vBool = False

		if TrimValue.lower() == "true" or TrimValue.isnumeric() and TrimValue == "1":
			vBool = True

		return vBool

	############################################################################################################
	#
	# handling the keyword None
	#
	# Basically the same than __assignStr__
	#
	def __assignNone__(self, value):
		TrimValue = self.__assignStr__(value)
		vNone = TrimValue

		if TrimValue.lower() == "none":
			vNone = ""

		return vNone

	############################################################################################################
	#
	# ensuring that type conversation will work
	#
	def __assignHexInt__(self, value):
		TrimValue = self.__assignStr__(value)
		iValue = 0

		try:
			if TrimValue:
				iValue = int(TrimValue, 16)

		except:
			print ("Some major error occured while converting Hex Value" + str(TrimValue) + " into int") 

		return iValue


	############################################################################################################
	#
	# ensuring that type conversation will work
	#
	def __assignInt__(self, value):
		TrimValue = self.__assignStr__(value)
		iValue = 0

		try:
			if TrimValue.isdigit():
				iValue = int(TrimValue)

			# 2019-11-17.. check on Hex value..
			elif TrimValue.find('x') or TrimValue.find('X'):
				iValue = self.__assignHexInt__(TrimValue)

		except:
			print ("Some major error occured while converting " + str(TrimValue) + " into int") 

		return iValue

	############################################################################################################
	#
	# ensuring that type conversation will work
	#
	def __assignIntPHPArray__(self, Array, value):
		TrimValue = self.__assignStr__(value)
		iValue = 0

		#print (value + "\n");
		try:
			if TrimValue.isdigit():
				iValue = int(TrimValue)

		except:
			print ("Some major error occured while converting " + str(TrimValue) + " into int") 

		Array.append(iValue)
		return 


	############################################################################################################
	#
	# ensuring that type conversation will work
	#
	def __assignFloat__(self, value):
		TrimValue = self.__assignStr__(value)
		fValue = 0.0
		
		try:
			fValue = float(TrimValue)
		except:
			print ("Some major error occured while converting " + str(TrimValue) + " into float") 

		return fValue


	############################################################################################################
	#
	# trimming a string
	#
	# Basically the same than __assignNone__
	#
	def __assignStr__(self, value):
		TrimValue = value.strip()

		# we have to remove the "
		TrimValue = TrimValue.replace("\"", "")

		return TrimValue.strip()

	def __assignStrArray__(self, value):
		ValueList = list()

		StrValue = self.__assignStr__(value)

		if StrValue:
			ValueList = [x.strip() for x in StrValue.split(',')]

		return ValueList

