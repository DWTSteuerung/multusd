<?php
# Karl Keusgen
# 2019-10-27
class StructModules 
{
	public $ModuleKey = "";
	public $ModuleIdentifier = "";
	public $ModuleDescription = "";
	public $ModulePHPHeadline = "";
	public $ModuleClass = "";
	public $ModuleConfig = "";
	public $EditRightLevel = array();
	Public $Enabled = False;
	// 2019-12-30
	Public $RunOnce = True;
	Public $RunInstances = 1;
	public $ModulePosition = 100;
	public $PHPPage = "";
	public $ModuleIsAService = False;
	public $ModuleBinary = "";
	public $ModuleStartScript = "";
	public $ModuleStartScriptParameter = "";
	public $ModuleStopScript = "";
	public $ModuleStopScriptParameter = "";
	public $ModuleStatusScript = "";
	public $ModuleStatusScriptParameter = "";
	public $ModuleControlPortEnabled = "";
	public $ModuleControlFileEnabled = "";
	public $ModuleControlMaxAge = 0.0;
	public $ModuleCheckScript = "";
	public $ModulePeriodicCheckInterval = 0;
}

if (isset($_SERVER['DOCUMENT_ROOT']) && $_SERVER['DOCUMENT_ROOT'])
	require_once($_SERVER['DOCUMENT_ROOT'] .'/Classes/ClassIniFunctions.php');
else
	include_once('/var/www/html/Classes/ClassIniFunctions.php');

class ClassModules extends ClassIniFunctions
{
	private $SortArray = array();	
	private $LocalArrayEnabledModules = array();
	public $ArrayEnabledModules = array();
	public $ArrayAllModules = array();

	function __construct($ConfigFile, $EditRightLevel) 
	{
		$this->ConfigFile = $ConfigFile;
		$this->EditRightLevel = $EditRightLevel;

		$this->__ReadModulesFile($this->ConfigFile, $EditRightLevel);
	}

	function __destruct() 
	{
		//print "Zerstoere " . __CLASS__ . "\n";
		;
    }

	
	function __ReadModulesFile($ConfigFile, $EditRightLevel)
	{
		// wir lesen die Config direkt mal ein
		$this->ini = parse_ini_file($ConfigFile, True);

		// Nachscahuen, welche Module fuer uns interessant sind

		#var_dump($this->ini);
		foreach($this->ini as $Key => $Section)
		{
			$Module = new StructModules;
			
			//print "Key: $Key \n";

			$Module->EditRightLevel = $Section['EditRightLevel'];
			$Module->Enabled = $Section['Enabled'];
			# 2019-12-30 more than 1 instance enabled
			if (isset($Section['RunOnce']))
			{
				$Module->RunOnce = $Section['RunOnce'];
				$Module->RunInstances = $Section['RunInstances'];
			}
			$Module->ModuleKey = $Key;
			$Module->ModuleIdentifier = trim($Section['ModuleIdentifier']);
			$Module->ModuleDescription = trim($Section['ModuleDescription']);
			$Module->ModulePHPHeadline = trim($Section['ModulePHPHeadline']);
			$Module->ModuleClass = trim($Section['ModuleClass']);
			$Module->ModuleConfig = trim($Section['ModuleConfig']);

			$Module->ModulePosition = $Section['ModulePosition'] ;
			$Module->PHPPage = trim($Section['PHPPage']);

			$Module->ModuleIsAService = trim($Section['ModuleIsAService']);
			$Module->ModuleBinary = trim($Section['ModuleBinary']);
			$Module->ModuleStartScript = trim($Section['ModuleStartScript']);
			$Module->ModuleStartScriptParameter = trim($Section['ModuleStartScriptParameter']);
			$Module->ModuleStopScript = trim($Section['ModuleStopScript']);
			$Module->ModuleStopScriptParameter = trim($Section['ModuleStopScriptParameter']);
			$Module->ModuleStatusScript = trim($Section['ModuleStatusScript']);
			$Module->ModuleStatusScriptParameter = trim($Section['ModuleStatusScriptParameter']);
			$Module->ModuleControlPortEnabled = trim($Section['ModuleControlPortEnabled']);
			$Module->ModuleControlFileEnabled = trim($Section['ModuleControlFileEnabled']);
			$Module->ModuleControlMaxAge = trim($Section['ModuleControlMaxAge']);
			$Module->ModuleCheckScript = trim($Section['ModuleCheckScript']);
			$Module->ModulePeriodicCheckInterval = $Section['ModulePeriodicCheckInterval'];
			
			$this->ArrayAllModules[] = $Module;

			print "PHPPage: $Module->PHPPage \n";

			if ($Section['Enabled'] && in_array($EditRightLevel, $Module->EditRightLevel) && $Module->PHPPage)
			{
				$this->LocalArrayEnabledModules[] = $Module;
				$this->SortArray[] = $Module->ModulePosition;
				//var_dump ($Section);
			}
		}

		// Wir haben alles intus.. jetzt sortieren
		//print "Before sorting\n";
		//var_dump ($this->SortArray);

		// NOw e got to sort the modules
		asort($this->SortArray);
		//print "After sorting\n";
		//var_dump ($this->SortArray);
		
		foreach ($this->SortArray as $key => $val)
		{
			//echo "$key = $val\n";	
			$this->ArrayEnabledModules[] = $this->LocalArrayEnabledModules[$key]; 
		}
		//var_dump ($this->ArrayEnabledModules);

	}
	
	function modifyValue($key, $parameter, $value)
	{
		$this->ini[$key][$parameter] = $value;
	}


	function WriteModulesIniFile()
	{
		print "We renew the Modules File";
		$this->writeIni($this->ini, $this->ConfigFile);
	}

}

?>
