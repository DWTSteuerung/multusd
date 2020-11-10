<?php 
// Karl Keusgen
// Massive rework for multus III
// Started alredy in 2016

function ReturnToLogin() 
{
	header ("Location: index.php");
}


// Session starten
session_name("DWTMultus");
session_start ();


if (! isset($_SESSION['ObjBasicInfos']))
	ReturnToLogin();

require $_SERVER['DOCUMENT_ROOT'] .'/Classes/ClassBasicInfos.php';
$ObjBasicInfos = unserialize(base64_decode($_SESSION['ObjBasicInfos']));

//print "<p>".$_SERVER['PHP_SELF']." Wir lesen jetzt die ClassUsers wieder ein</p>";
require $_SERVER['DOCUMENT_ROOT'] .$ObjBasicInfos->multusUsersClass;
$ObjUsers = unserialize(base64_decode($_SESSION['ObjUsers']));

//var_dump($ObjUsers);

// first we check on a valid session and vailid object
if ( ! isset($ObjUsers))
{
	ReturnToLogin();
}
else
{
	// now the User Object is valid, we cahck the validity of th elogin
	if ($ObjUsers->CurrentUserValid)
	{
		//We have an valid user, so we can do all the stuffe we need in every position
		header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
		header("Cache-Control: post-check=0, pre-check=0", false);
		header("Pragma: no-cache");

	}
	else
	{
		ReturnToLogin();
	}
}
?>


