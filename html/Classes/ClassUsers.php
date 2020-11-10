<?php
# Karl Keusgen
# 2019-10-27

class ClassUsers 
{
	public $CurrentUserValid = False;
	public $CurrentUser = "" ;
	public $CurrentEditRightLevel = 999;

	private $ini;

	function __construct($ConfigFile) 
	{
		## wir lesen die Config direkt mal ein
		$this->ini = parse_ini_file($ConfigFile, True);

		#var_dump($ini);

	}

	function __destruct() 
	{
		//print "Zerstoere " . __CLASS__ . "\n";
		$this->CurrentUserValid = False;
		$this->CurrentUser = "" ;
		$this->CurrentEditRightLevel = 999;
    }

	function __EncryptPassword($PWD)
	{
		return md5("Abc5".$_REQUEST['pwd']."SuperHansel");
	}

	function CheckPasswort($UserName, $Password)
	{
		//print "Entered function CheckPasswort \n";
		
		$PasswortValid = False;

		foreach($this->ini as $Section)
		{
			if ($Section['username'] == $UserName)
			{
				##var_dump($Section);
				$EncryptedPassWord = $this->__EncryptPassword($Password);
				if ($EncryptedPassWord == $Section['password'])
				{
					$this->CurrentUser = $Section['username'];
					$this->CurrentEditRightLevel = $Section['right_level'];
					$this->CurrentUserValid = True;
					$PasswortValid = True;
					//print "<p>We got the valid user: $this->CurrentUser</p>";
					break;
				}
			}
		}

		#return list($PasswortValid, $UserEditRightLevel);
		return $PasswortValid;
	}

	function __WriteUserFile()
	{
		print "We renew the User File";
	}

	function ChangeUserPasswort($Passwort)
	{
		print "Entered function CheckPasswort \n";

		$this->__WriteUserFile();
	}

}
?>
