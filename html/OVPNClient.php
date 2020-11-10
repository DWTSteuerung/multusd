<?php 
// Karl Keusgen
// Massive rework for multus III
// 2019-11-04
//

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "multusOVPNClient";
$SessionClassIdentifier = $PageIdentifier;

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';

// 2019-12-30
// Now, we know the numbers of instrances, this process may have
if ($RunOnce == False)
{
	print ("<br>Process should run a number of instances: $RunInstances <br>");
	$Instance = 0;
	if (isset($_GET['Instance']))
		$Instance = $_GET['Instance'];

	echo "<div id='tabsK'>";
		echo "<ul>";
			for ($i = 0; $i < $RunInstances; $i++)
			if ($i == $Instance)
				echo '<li id=current><a href="'.$_SERVER['PHP_SELF'].'?Instance='.$Instance.'"><span>'.$ModulePHPHeadline.'_'.$Instance.'</span></a></li>';
			else
				echo '<li><a href="'.$_SERVER['PHP_SELF'].'?Instance='.$i.'"><span>'.$ModulePHPHeadline.'_'.$i.'</span></a></li>';

		echo '</ul>';
	echo '</div>'; // tabsK


	$SessionClassIdentifier = $SessionClassIdentifier."_".$Instance;
	$ConfigFileArray = explode(".", $PageConfig);
	$PageConfig = $ConfigFileArray[0]."_".$Instance.".".$ConfigFileArray[1];

	echo "<form method=post name='FormEreignis' action='".$_SERVER['PHP_SELF']."?Instance=$Instance'>";
}

// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if ( ! isset($_SESSION[$SessionClassIdentifier]))
{
	print "<p>Class $SessionClassIdentifier not in session, we create a new instance<p>";
	$ObjmultusOVPNClientClass = new ClassmultusOVPNClient($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $PageIdentifier, $RunOnce, $Instance);
}
else
{
	$ObjmultusOVPNClientClass = unserialize(base64_decode($_SESSION[$SessionClassIdentifier]));
}

// check on prior action
$ObjmultusOVPNClientClass->HandleApplyButton();

if ($ObjmultusOVPNClientClass->bIniNeedsToBeWritten)
{
	// Save changes into session
	$_SESSION[$SessionClassIdentifier] = base64_encode(serialize($ObjmultusOVPNClientClass)); 

	$ObjmultusOVPNClientClass->writeIni($ObjmultusOVPNClientClass->ini, $PageConfig);
}

$ObjmultusOVPNClientClass->HandleChangesToRestart();


/////// Now here comes the html stuff and the selction
$ObjmultusOVPNClientClass->PutTheTable();

if (!$ObjmultusOVPNClientClass->bIniNeedsToBeWritten)
	$ObjmultusOVPNClientClass->PutReLoadButton();

/////// Put the RebootButton
$ObjmultusOVPNClientClass->PutRebootButtons();


// we store the class data in the session
$_SESSION[$SessionClassIdentifier] = base64_encode(serialize($ObjmultusOVPNClientClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
