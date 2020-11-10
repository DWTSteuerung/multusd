<?php 
// Karl Keusgen
// Massive rework for multus III
// Started already in 2016

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "Hardware";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';


// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION['ObjHardwareClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjHardwareClass = new ClassHardware($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier);

}
else
{
	$ObjHardwareClass = unserialize(base64_decode($_SESSION['ObjHardwareClass']));
}

/////// 2019-10-31

// check on prior action
$ObjHardwareClass->HandleApplyButton();

if ($ObjHardwareClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION['ObjHardwareClass'] = base64_encode(serialize($ObjHardwareClass)); 

	$ObjHardwareClass->writeIni($ObjHardwareClass->ini, $PageConfig);
}


/////// Now here comes the html stuff and the selction
$ObjHardwareClass->PutTheTable();

/////// Put the RebootButton
$ObjHardwareClass->PutRebootButtons();

// we store the class data in the session
$_SESSION['ObjHardwareClass'] = base64_encode(serialize($ObjHardwareClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
