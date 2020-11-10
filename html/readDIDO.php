<?php 
// Karl Keusgen
// Massive rework for multus III
// 2019-11-04
//

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "multusReadDIDO";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';


// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION['ObjmultusReadDIDOClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjmultusReadDIDOClass = new ClassmultusReadDIDO($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier);
}
else
{
	$ObjmultusReadDIDOClass = unserialize(base64_decode($_SESSION['ObjmultusReadDIDOClass']));
}

// check on prior action
$ObjmultusReadDIDOClass->HandleApplyButton();

if ($ObjmultusReadDIDOClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION['ObjmultusReadDIDOClass'] = base64_encode(serialize($ObjmultusReadDIDOClass)); 

	$ObjmultusReadDIDOClass->writeIni($ObjmultusReadDIDOClass->ini, $PageConfig);
}

$ObjmultusReadDIDOClass->HandleChangesToRestart();


/////// Now here comes the html stuff and the selction
$ObjmultusReadDIDOClass->PutTheTable();

/////// Put the RebootButton
$ObjmultusReadDIDOClass->PutRebootButtons();


// we store the class data in the session
$_SESSION['ObjmultusReadDIDOClass'] = base64_encode(serialize($ObjmultusReadDIDOClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
