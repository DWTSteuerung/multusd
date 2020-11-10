<?php 
// Karl Keusgen
// Massive rework for multus III
// 2019-11-04
//

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "multusModbus";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';


// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION['ObjmultusModbusClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjmultusModbusClass = new ClassmultusModbus($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier);
}
else
{
	$ObjmultusModbusClass = unserialize(base64_decode($_SESSION['ObjmultusModbusClass']));
}

// check on prior action
$ObjmultusModbusClass->HandleApplyButton();

if ($ObjmultusModbusClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION['ObjmultusModbusClass'] = base64_encode(serialize($ObjmultusModbusClass)); 

	$ObjmultusModbusClass->writeIni($ObjmultusModbusClass->ini, $PageConfig);
}

$ObjmultusModbusClass->HandleChangesToRestart();


/////// Now here comes the html stuff and the selction
$ObjmultusModbusClass->PutTheTable();

/////// Put the RebootButton
$ObjmultusModbusClass->PutRebootButtons();


// we store the class data in the session
$_SESSION['ObjmultusModbusClass'] = base64_encode(serialize($ObjmultusModbusClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
