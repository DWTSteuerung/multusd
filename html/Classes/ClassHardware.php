<?php
// Karl Keusgen
// 2019-10-29
//

if (isset($_SERVER['DOCUMENT_ROOT']) && $_SERVER['DOCUMENT_ROOT'])
	require_once ($_SERVER['DOCUMENT_ROOT'] .'/Classes/ClassIniFunctions.php');
else
	include_once('/var/www/html/Classes/ClassIniFunctions.php');


class ClassHardware extends ClassIniFunctions
{
	function __construct($ConfigFile, $EditRightLevel, $Heading, $PageIdentifier) 
	{
		$this->EditRightLevel = $EditRightLevel;
		$this->Heading = $Heading; 
		$this->ConfigFile = $ConfigFile;	
		$this->UpdateDirectory = $this->UpdateDirectory."/".$PageIdentifier;

		// read the config
		print "Now we read in the Config: $this->ConfigFile<br>";
		$this->ReadConfigFile($this->ConfigFile);
	}

	function __destruct() 
	{
		;
	}
}

?>
