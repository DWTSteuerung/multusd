<?php 
// Karl Keusgen
// Massive rework for multus III
// Started already in 2016

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "multusLAN";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';


// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION['ObjNetworkClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjNetworkClass = new ClassNetwork($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier);
}
else
{
	$ObjNetworkClass = unserialize(base64_decode($_SESSION['ObjNetworkClass']));
}


/////// 2019-10-31

// check on prior action
$ObjNetworkClass->HandleApplyButton();

if ($ObjNetworkClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION['ObjNetworkClass'] = base64_encode(serialize($ObjNetworkClass)); 

	$ObjNetworkClass->writeIni($ObjNetworkClass->ini, $PageConfig);
}

$ObjNetworkClass->HandleChangesToRestart();

print ("<p>");
print ("Local IP-Adresses are currently: ");
#$localIP = system("ip addr show eth0 | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1", $retval);
$localIP = system("ip addr | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1", $retval);
print ("</p>");

/////// Now here comes the html stuff and the selction
$ObjNetworkClass->PutTheTable();

/////// Put the RebootButton
$ObjNetworkClass->PutRebootButtons();


// we store the class data in the session
$_SESSION['ObjNetworkClass'] = base64_encode(serialize($ObjNetworkClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
