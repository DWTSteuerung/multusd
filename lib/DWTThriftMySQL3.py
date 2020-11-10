# -*- coding: utf-8 -*-
# Karl Keusgen
# 2019-04-29
#
# port to python3 on 2019-10-24
#
# 2019-11-23
# extened it by logging on table multusReadDO 
#

class ThriftMySQL(object):

	############################################################################################################
	def __init__(self, Config, DWTThriftToolsInstance):
		self.Config = Config
		self.Tools = DWTThriftToolsInstance

		self.Tools.logger.debug("MySQL Logger Class: Initialisierung")
		
	############################################################################################################
	def _del__(self):
		self.Tools.logger.debug( "Exiting MySQl Logger Class")

	############################################################################################################
	###
	### 2019-05-03
	def InitLastValues(self):
		mysqlCon, cursor = self.Tools.OpenMySQL(self.Config.ThriftMysqlOpts)
		self.LatestDIs = self.__GetLatestStatus__(cursor, "multusDI", "INDEX_DI")
		self.LatestDOs = self.__GetLatestStatus__(cursor, "multusDO", "INDEX_DO")
		self.Tools.CloseMySQL(mysqlCon, cursor)

		return
	
	############################################################################################################
	###
	### 2019-11-23
	def InitLastReadDOValues(self):
		mysqlCon, cursor = self.Tools.OpenMySQL(self.Config.ThriftMysqlOpts)
		self.LatestRDOs = self.__GetLatestStatus__(cursor, "multusReadDO", "INDEX_RDO")
		self.Tools.CloseMySQL(mysqlCon, cursor)

	############################################################################################################
	###
	### 2019-05-03
	### Die Address variable wird aktuell noch nicht verwendet.
	### Wenn die Protokolierung auf mehr als die beiden 0 Baenke ausgedehnt wird, 
	### dann muss erst mal eine Lookup tabelle in dee DOs und DIs an der System
	### zur verfuegung stehen in der Datenbank hinterlegt werden
	def ReadLastDOMySQL(self, Address):

		LastDO = list()	

		### Die self.LatestDOs wurden ja gerade erst eingelesen..
		### muss noch invertiert werden
		for Element in self.LatestDOs:
			if Element == 1:
				LastDO.append(0)
			else:
				LastDO.append(1)

		return LastDO

	############################################################################################################
	def __CloseLatestStatus__(self, cursor, table):
		## 2020-01-01
		## suddenly the old  sysdate() - DI_StatusChange clause did not work any more.. we had to add the unixdate function
		## strange.. on 2019-12-31 it worked that way..

		if table == "multusDI":
			SQL = "select INDEX_DI, unix_timestamp(sysdate()) - unix_timestamp(DI_StatusChange) from multusDI order by INDEX_DI desc limit 1"
		elif table == "multusDO":
			SQL = "select INDEX_DO, unix_timestamp(sysdate()) - unix_timestamp(DO_StatusChange) from multusDO order by INDEX_DO desc limit 1"
		elif table == "multusReadDO":
			SQL = "select INDEX_RDO, unix_timestamp(sysdate()) - unix_timestamp(RDO_StatusChange) from multusReadDO order by INDEX_RDO desc limit 1"

		cursor.execute(SQL)
		data=cursor.fetchone()
		
		if table == "multusDI":
			SQL = "update multusDI set DI_Duration=" + str(int(data[1])) + " where INDEX_DI=" + str(data[0])
			self.Tools.logger.debug("Close old multusDI Event in INDEX_DI: " + str(data[0]) + " Duration: " + str(data[1]))
		elif table == "multusDO":
			SQL = "update multusDO set DO_Duration=" + str(int(data[1])) + " where INDEX_DO=" + str(data[0])
			self.Tools.logger.debug("Close old multusDO Event in INDEX_DIO " + str(data[0]) + " Duration: " + str(data[1]))
		elif table == "multusReadDO":
			SQL = "update multusReadDO set RDO_Duration=" + str(int(data[1])) + " where INDEX_RDO=" + str(data[0])
			self.Tools.logger.debug("Close old multusDO Event in INDEX_DIO " + str(data[0]) + " Duration: " + str(data[1]))

		#print ("__CloseLatestStatus__ Table: " + table + " SQL: " + SQL)
		cursor.execute(SQL)
		return

	############################################################################################################
	def __GetLatestStatus__(self, cursor, table, OrderIndex):
		
		SQL="select * from " + table + " order by " + OrderIndex + " desc limit 1"
		cursor.execute(SQL)
		data=cursor.fetchone()

		DigitalStatus = list()
		i = 1
		while i < 9:
					
			try:
				if len(data[i]):
					DigitalStatus.append(int(data[i]))
				else:
					DigitalStatus.append(0)

			except:
				DigitalStatus.append(0)
				
			#self.Tools.logger.debug( "__GetLatestStatus__: " + table + " Alter Status nach Typenumwandlung: Nr. " + str(i) + " '" + str(data[i]) + "'"  + " Darauf haben wir zum Vergleich das hier gemacht: " + str(DigitalStatus[i - 2])

			i = i + 1
		
		return DigitalStatus
		
	############################################################################################################
	def __CompareStatus__(self, DOld, DNew):
		bDiffer = False

		i = 0
		while i < 8:
			## Es muessen 0 oder 1 verblichen werden -1 kann nicht verglichen werden
			if DOld[i] != DNew[i]:
				#self.Tools.logger.debug("Hallo")
				#self.Tools.logger.debug("Unterschied: Neu: " + str(DNew[i]) + " Datenbank: " + str(DOld[i]))
				bDiffer = True
			#else:
				#self.Tools.logger.debug("Kein Unterschied: Neu: " + str(DNew[i]) + " Datenbank: " + str(DOld[i]))

			i = i + 1	

		#self.Tools.logger.debug( "__CompareStatus__: Vergleich Ergebnis: " + str(bDiffer))
		#print DOld
		#print DNew

		return bDiffer

	###################
	## 2019-11-23
	def LogReadDOEvent(self, gRDOs):
	
		RDOs = list()
		
		## Wir muessen die Polatitaet noch invertieren
		## Innerhalb dieser Klasse bedeutet 1: Ausgang gesetzt.. 
		## In der Hardware ist sonst umgekehrte Logik.. hier aber nicht
		i = 0
		while i < 8:
			if gRDOs[i] == 0:
				RDOs.append(0)

			elif gRDOs[i] == 1:
				RDOs.append(1)

			## Unbestimmt -1 .. dann nehmen wir den alten Zustand
			else:
				RDOs.append(self.LatestRDOs[i])

			i = i + 1
	
		### Vergleich mit dem letzten Status
		bUpdateNeeded = self.__CompareStatus__(self.LatestRDOs, RDOs)

		if bUpdateNeeded:
			mysqlCon, cursor = self.Tools.OpenMySQL(self.Config.ThriftMysqlOpts)

			## Zuerst muessen wir den alten Status abschließen
			self.__CloseLatestStatus__(cursor, "multusReadDO")

			## wir heben einen neuen Status, den tragen wir jetzt in die DB ein
			SQL = "insert into multusReadDO set RDO1_Status = '" +  str(RDOs[0]) + "', RDO2_Status = '" + str(RDOs[1]) + "', RDO3_Status = '" + str(RDOs[2]) + "', RDO4_Status = '" + str(RDOs[3]) + "', RDO5_Status = '" + str(RDOs[4]) + "', RDO6_Status = '" + str(RDOs[5]) + "', RDO7_Status = '" + str(RDOs[6]) + "', RDO8_Status = '" + str(RDOs[7]) + "', RDO_StatusChange = sysdate()"

			cursor.execute(SQL)

			self.Tools.CloseMySQL(mysqlCon, cursor)

			## Neuer letzter Status
			self.LatestRDOs = RDOs
			self.Tools.logger.debug("MySQL Logger: ReadDO Status changed.. updated")


		return


	############################################################################################################
	### Triggerd by thrift request
	def LogDOEvent(self, gDOs):
	
		DOs = list()
		
		## Wir muessen die Polatitaet noch invertieren
		## Innerhalb dieser Klasse bedeutet 1: Ausgang gesetzt.. 
		## In der Hardware ist sonst umgekehrte Logik.. hier aber nicht
		i = 0
		while i < 8:
			if gDOs[i] == 1:
				DOs.append(0)

			elif gDOs[i] == 0:
				DOs.append(1)

			## Unbestimmt -1 .. dann nehmen wir den alten Zustand
			else:
				DOs.append(self.LatestDOs[i])

			i = i + 1
	
		### Vergleich mit dem letzten Status
		bUpdateNeeded = self.__CompareStatus__(self.LatestDOs, DOs)

		if bUpdateNeeded:
			mysqlCon, cursor = self.Tools.OpenMySQL(self.Config.ThriftMysqlOpts)

			## Zuerst muessen wir den alten Status abschließen
			self.__CloseLatestStatus__(cursor, "multusDO")

			## wir heben einen neuen Status, den tragen wir jetzt in die DB ein
			SQL = "insert into multusDO set DO1_Status = '" +  str(DOs[0]) + "', DO2_Status = '" + str(DOs[1]) + "', DO3_Status = '" + str(DOs[2]) + "', DO4_Status = '" + str(DOs[3]) + "', DO5_Status = '" + str(DOs[4]) + "', DO6_Status = '" + str(DOs[5]) + "', DO7_Status = '" + str(DOs[6]) + "', DO8_Status = '" + str(DOs[7]) + "', DO_StatusChange = sysdate()"

			cursor.execute(SQL)

			self.Tools.CloseMySQL(mysqlCon, cursor)

			## Neuer letzter Status
			self.LatestDOs = DOs
			self.Tools.logger.debug("MySQL Logger: DO Status changed.. updated")


		return

	############################################################################################################
	### Triggerd by thrift request
	def LogDIEvent(self, gDIs):
	
		DIs = list()

		## Wir muessen die Polatitaet noch invertieren
		### Der Funktionsoaufruf ist call by Refecence.. damit wir die OriginalWerte nicht aendern
		i = 0
		for Element in gDIs:
			if Element == 1:
				DIs.append(0)
			elif Element == 0:
				DIs.append(1)

			## Unbestimmt -1 .. dann nehmen wir den alten Zustand
			else:
				DIs.append(self.LatestDIs[i])

			i = i + 1

		bUpdateNeeded = self.__CompareStatus__(self.LatestDIs, DIs)

		if bUpdateNeeded:
			## wir heben einen neuen Status, den tragen wir jetzt in die DB ein
			mysqlCon, cursor = self.Tools.OpenMySQL(self.Config.ThriftMysqlOpts)
		
			## Zuerst muessen wir den alten Status abschließen
			self.__CloseLatestStatus__(cursor, "multusDI")

			SQL = "insert into multusDI set DI1_Status = '" +  str(DIs[0]) + "', DI2_Status = '" + str(DIs[1]) + "', DI3_Status = '" + str(DIs[2]) + "', DI4_Status = '" + str(DIs[3]) + "', DI5_Status = '" + str(DIs[4]) + "', DI6_Status = '" + str(DIs[5]) + "', DI7_Status = '" + str(DIs[6]) + "', DI8_Status = '" + str(DIs[7]) + "', DI_StatusChange = sysdate()"

			cursor.execute(SQL)
			self.LatestDIs = DIs

			self.Tools.logger.debug("MySQL Logger: DI Status changed.. updated")

			self.Tools.CloseMySQL(mysqlCon, cursor)

		return
