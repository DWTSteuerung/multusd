<?php 
// Karl Keusgen
// Massive rework for multus III
// 2019-11-04
//

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "StatusLED";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';


// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION['ObjStatusLEDClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjStatusLEDClass = new ClassStatusLED($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier);
}
else
{
	$ObjStatusLEDClass = unserialize(base64_decode($_SESSION['ObjStatusLEDClass']));
}

// check on prior action
$ObjStatusLEDClass->HandleApplyButton();

if ($ObjStatusLEDClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION['ObjStatusLEDClass'] = base64_encode(serialize($ObjStatusLEDClass)); 

	$ObjStatusLEDClass->writeIni($ObjStatusLEDClass->ini, $PageConfig);
}

$ObjStatusLEDClass->HandleChangesToRestart();


/////// Now here comes the html stuff and the selction
$ObjStatusLEDClass->PutTheTable();

/////// Put the RebootButton
$ObjStatusLEDClass->PutRebootButtons();


// we store the class data in the session
$_SESSION['ObjStatusLEDClass'] = base64_encode(serialize($ObjStatusLEDClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
