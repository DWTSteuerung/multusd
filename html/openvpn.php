<?php 
// Karl Keusgen
// Massive rework for multus III
// Started already in 2016

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "OpenVPNCheck";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';


// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION['ObjOpenVPNCheckClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjOpenVPNCheckClass = new ClassOpenVPNCheck($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier);
}
else
{
	$ObjOpenVPNCheckClass = unserialize(base64_decode($_SESSION['ObjOpenVPNCheckClass']));
}

/////// 2019-10-31

// check on prior action
$ObjOpenVPNCheckClass->HandleApplyButton();

if ($ObjOpenVPNCheckClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION['ObjOpenVPNCheckClass'] = base64_encode(serialize($ObjOpenVPNCheckClass)); 

	$ObjOpenVPNCheckClass->writeIni($ObjOpenVPNCheckClass->ini, $PageConfig);
}

$ObjOpenVPNCheckClass->HandleChangesToRestart();

/////// Now here comes the html stuff and the selction
$ObjOpenVPNCheckClass->PutTheTable();

/////// Put the RebootButton
$ObjOpenVPNCheckClass->PutRebootButtons();


// we store the class data in the session
$_SESSION['ObjOpenVPNCheckClass'] = base64_encode(serialize($ObjOpenVPNCheckClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
