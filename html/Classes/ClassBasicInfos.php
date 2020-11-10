<?php
# Karl Keusgen
# 2019-10-27

class ClassBasicInfos
{
	public $SiteIdentifier = "" ;

	public $multusUsersConfigFile = "";
	public $multusUsersClass = "";
	public $multusModulesConfigFile = "";
	public $multusModulesClass = "";

	// Die einzig hart codierte Config datei
	private static $CONFIG_FILE = "/multus/etc/multusd.conf";
	private $ini;

	function __construct() 
	{
		## wir lesen die Config direkt mal ein
		$this->ini = parse_ini_file(self::$CONFIG_FILE, True);
		$this->SiteIdentifier = "Deutsche Windtechnik BNK-Box";
		##$this->SiteIdentifier = $this->ini['DEFAULT']['Site'];
		$this->multusUsersConfigFile = $this->ini['BasicClasses']['multusUsersConfigFile'];
		$this->multusUsersClass = $this->ini['BasicClasses']['multusUsersClass'];
		$this->multusModulesConfigFile = $this->ini['BasicClasses']['multusModulesConfigFile'] ;
		$this->multusModulesClass = $this->ini['BasicClasses']['multusModulesClass'] ;
		//var_dump($this->ini);

	}

	function __destruct() 
	{
		//print "Zerstoere " . __CLASS__ . "\n";
		$this->SiteIdentifier = "";
    }
}
?>
