--
-- Karl Keusgen
-- 2018-12-05 BNK database
-- 

drop database if exists multusModbus;
create database multusModbus;

use multusModbus

DROP TABLE IF EXISTS `multusDO`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `multusDO` (
  `INDEX_DO` int(10) unsigned NOT NULL auto_increment,
  `DO1_Status` enum('0', '1') default '0',
  `DO2_Status` enum('0', '1') default '0',
  `DO3_Status` enum('0', '1') default '0',
  `DO4_Status` enum('0', '1') default '0',
  `DO5_Status` enum('0', '1') default '0',
  `DO6_Status` enum('0', '1') default '0',
  `DO7_Status` enum('0', '1') default '0',
  `DO8_Status` enum('0', '1') default '0',
  `DO_StatusChange` datetime default '0000-00-00 00:00:00',
  `DO_Duration` int(10) default 0,
  `DO_TU_Index` int(10) default 0,
  `DO_Address` int(3) default 0,
   KEY `INDEX_DO` (`INDEX_DO`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

DROP TABLE IF EXISTS `multusReadDO`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `multusReadDO` (
  `INDEX_RDO` int(10) unsigned NOT NULL auto_increment,
  `RDO1_Status` enum('0', '1') default '0',
  `RDO2_Status` enum('0', '1') default '0',
  `RDO3_Status` enum('0', '1') default '0',
  `RDO4_Status` enum('0', '1') default '0',
  `RDO5_Status` enum('0', '1') default '0',
  `RDO6_Status` enum('0', '1') default '0',
  `RDO7_Status` enum('0', '1') default '0',
  `RDO8_Status` enum('0', '1') default '0',
  `RDO_StatusChange` datetime default '0000-00-00 00:00:00',
  `RDO_Duration` int(10) default 0,
  `RDO_TU_Index` int(10) default 0,
  `RDO_Address` int(3) default 0,
   KEY `INDEX_RDO` (`INDEX_RDO`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

DROP TABLE IF EXISTS `multusDI`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `multusDI` (
  `INDEX_DI` int(10) unsigned NOT NULL auto_increment,
  `DI1_Status` enum('0', '1') default '0',
  `DI2_Status` enum('0', '1') default '0',
  `DI3_Status` enum('0', '1') default '0',
  `DI4_Status` enum('0', '1') default '0',
  `DI5_Status` enum('0', '1') default '0',
  `DI6_Status` enum('0', '1') default '0',
  `DI7_Status` enum('0', '1') default '0',
  `DI8_Status` enum('0', '1') default '0',
  `DI_StatusChange` datetime default '0000-00-00 00:00:00',
  `DI_Duration` int(10) default 0,
  `DI_Address` int(3) default 0,
   KEY `INDEX_DI` (`INDEX_DI`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;
