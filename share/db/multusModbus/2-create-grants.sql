--
-- Karl Keusgen
-- 2013-03-07 Pixelterminal Datenbank anlegen
-- 


GRANT SELECT, INSERT, UPDATE, DELETE ON multusModbus.multusDO TO 'admin'@'localhost'; 
GRANT SELECT, INSERT, UPDATE, DELETE ON multusModbus.multusReadDO TO 'admin'@'localhost'; 
GRANT SELECT, INSERT, UPDATE, DELETE ON multusModbus.multusDI TO 'admin'@'localhost';
