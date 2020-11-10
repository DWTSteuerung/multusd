<?php 
// Karl Keusgen
// Massive rework for multus III
// 2019-11-03
//

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "Site";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';


// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION['ObjSiteClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjSiteClass = new ClassSite($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier);
}
else
{
	$ObjSiteClass = unserialize(base64_decode($_SESSION['ObjSiteClass']));
}

// check on prior action
$ObjSiteClass->HandleApplyButton();

if ($ObjSiteClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION['ObjSiteClass'] = base64_encode(serialize($ObjSiteClass)); 

	$ObjSiteClass->writeIni($ObjSiteClass->ini, $PageConfig);
}


/////// Now here comes the html stuff and the selction
$ObjSiteClass->PutTheTable();

/////// Put the RebootButton
$ObjSiteClass->PutRebootButtons();


// we store the class data in the session
$_SESSION['ObjSiteClass'] = base64_encode(serialize($ObjSiteClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
