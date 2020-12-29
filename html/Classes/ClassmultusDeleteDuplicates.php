<?php
// Karl Keusgen
// 2020-12-28
//

if (isset($_SERVER['DOCUMENT_ROOT']) && $_SERVER['DOCUMENT_ROOT'])
	require_once ($_SERVER['DOCUMENT_ROOT'] .'/Classes/ClassIniFunctions.php');
else
	include_once('/var/www/html/Classes/ClassIniFunctions.php');


class ClassmultusDeleteDuplicates extends ClassIniFunctions
{
	function __construct($ConfigFile, $EditRightLevel, $Heading, $PageIdentifier, $RunOnce, $Instance) 
	{
		$this->EditRightLevel = $EditRightLevel;
		$this->Heading = $Heading;
		$this->ConfigFile = $ConfigFile;	
		$this->RunOnce = $RunOnce;
		$this->Instance = $Instance;
		# full path
		if ($this->RunOnce)
			$this->UpdateDirectory = $this->UpdateDirectory."/".$PageIdentifier;
		else
			$this->UpdateDirectory = $this->UpdateDirectory."/".$PageIdentifier."_".$Instance;

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
