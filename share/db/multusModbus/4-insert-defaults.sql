use multusModbus;

insert into multusReadDO set RDO1_Status = '0', RDO2_Status = '0', RDO3_Status = '0', RDO4_Status = '0', RDO5_Status = '0', RDO6_Status = '0', RDO7_Status = '0', RDO8_Status = '0', RDO_StatusChange = sysdate();

insert into multusDO set DO1_Status = '0', DO2_Status = '0', DO3_Status = '0', DO4_Status = '0', DO5_Status = '0', DO6_Status = '0', DO7_Status = '0', DO8_Status = '0', DO_StatusChange = sysdate();

insert into multusDI set DI1_Status = '0', DI2_Status = '0', DI3_Status = '0', DI4_Status = '0', DI5_Status = '0', DI6_Status = '0', DI7_Status = '0', DI8_Status = '0', DI_StatusChange = sysdate();
