<?php
// Karl Keusgen
// 2019-11-04
//

if (isset($_SERVER['DOCUMENT_ROOT']) && $_SERVER['DOCUMENT_ROOT'])
	require_once ($_SERVER['DOCUMENT_ROOT'] .'/Classes/ClassIniFunctions.php');
else
	include_once('/var/www/html/Classes/ClassIniFunctions.php');


class ClassStatusLED extends ClassIniFunctions
{
	function __construct($ConfigFile, $EditRightLevel, $Heading, $PageIdentifier) 
	{
		$this->EditRightLevel = $EditRightLevel;
		$this->Heading = $Heading;
		$this->ConfigFile = $ConfigFile;	
		# full path
		$this->UpdateDirectory = $this->UpdateDirectory."/".$PageIdentifier;

		// read the config
		print "Now we read in the Config: $this->ConfigFile<br>";
		$this->ReadConfigFile($this->ConfigFile);

	}

	function __destruct() 
	{
		;
	}

	function HandleChangesToRestart()
	{
		if ($this->ChangedKeys)
		{
			print ("<h4> We request a process restart </h4>");
			$ReloadFile = $this->UpdateDirectory."/Reload";

			touch($ReloadFile);
			chmod($ReloadFile, 0666);

			// reset arry of changes to prevent multible restarts
			$this->ChangedKeys = [];
		}
	}
}

?>
