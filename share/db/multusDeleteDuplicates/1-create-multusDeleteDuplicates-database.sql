--
-- Karl Keusgen
-- 2018-12-05 BNK database
-- 

drop database if exists multusDeleteDuplicates;
create database multusDeleteDuplicates;

use multusDeleteDuplicates

DROP TABLE IF EXISTS `BasicPath`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `BasicPath` (
  `INDEX_BP` int(3) unsigned NOT NULL auto_increment,
  `BP_Path` varchar(256),
  `BP_TSCreated` datetime,
   KEY `INDEX_BP` (`INDEX_BP`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

DROP TABLE IF EXISTS `ExtendedPath`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `ExtendedPath` (
  `INDEX_EP` int(6) unsigned NOT NULL auto_increment,
  `EP_Index_BP` int(3) unsigned,
  `EP_Path` varchar(256),
  `EP_TSCreated` datetime,
   KEY `INDEX_EP` (`INDEX_EP`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

DROP TABLE IF EXISTS `Files`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `Files` (
  `INDEX_FI` int(10) unsigned NOT NULL auto_increment,
  `FI_Index_EP` int(6) unsigned,
  `FI_FileName` varchar(1024),
  `FI_MD5Sum` varchar(64) default '',
  `FI_TSChanged` datetime,
  `FI_DoubleIndex` int(10) default '0',
  `FI_TSCreated` datetime,
  `FI_Deleted` enum('0', '1') default '0',
  `FI_TSDeleted` datetime,
   KEY `INDEX_FI` (`INDEX_FI`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;
