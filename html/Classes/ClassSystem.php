<?php
// Karl Keusgen
// 2019-10-29
//

class ClassSystem extends ClassIniFunctions
{
	function __construct($ConfigFile, $PageIdentifier) 
	{
		if ($ConfigFile)
			$this->ini = parse_ini_file($ConfigFile, True);

		$this->UpdateDirectory = $this->UpdateDirectory."/system";
	
	}

	function __destruct() 
	{
		;
	}

	function GetRunningStatus ($Module)
	{
		$strRunningStatus = "unknown";

		if ($Module->ModuleBinary)
		{
			//2019-12-30
			// if there are more instances.. build the name of the binaries
			$Instance = 0;
			$strRunningStatus = "";
			
			// Make sure loop is running only once if there are no instances
			if ($Module->RunOnce)
				$Module->RunInstances = 1;

			$ModuleBinary = $Module->ModuleBinary;
			for ($i = 0; $i < $Module->RunInstances; $i++)
			{
				// Build filename of singel instances
				if ($Module->RunOnce == False)
				{
					$AB	= explode(".", $Module->ModuleBinary);
					$ModuleBinary = $AB[0].'_'.$i.'.'.$AB[1];
					//print ("looking for binary: $ModuleBinary");
				}

				ob_start();
				system(" /bin/ps -ax | /bin/grep ".$ModuleBinary." | /bin/grep -v grep | /bin/grep -v vim", $returnCode);
				$output = ob_get_clean();	
			
				if (strlen($strRunningStatus))
					$strRunningStatus = $strRunningStatus."<br>";
					
				if ($returnCode == 0)
					$strRunningStatus = $strRunningStatus.$i.": OK";
				else
					$strRunningStatus = $strRunningStatus.$i.": Failure";
			}

		}
		elseif ($Module->ModuleStatusScript)
		{
			// We buffer the output of executon of the script
			ob_start();
			system($Module->ModuleStatusScript." ".$Module->ModuleStatusScriptParameter, $returnCode);
			$output = ob_get_clean();	

			// print ("<h4>$Module->ModuleStatusScript Return code $returnCode <br>$output</h4>");
			
			if ($returnCode == 0)
				$strRunningStatus = "OK";
			else
				$strRunningStatus = "Failure";

		}

		return $strRunningStatus;

	}

	function ScheduleRestart($Module)
	{
		### TODO
		;
	}
	
	function ScheduleReloadmultusd()
	{
		$ReloadFile = $this->UpdateDirectory."/Reload.Modules";

		print ("<p> We request a multusd module reload</p>");

		touch($ReloadFile);
		chmod($ReloadFile, 0666);

	}

}

?>

