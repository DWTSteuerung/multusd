<?php 
// Karl Keusgen
// Massive rework for multus III
// Started already in 2016

require $_SERVER['DOCUMENT_ROOT'] .'/CheckUser.php';

// has to be the same, then the identifier in the moduels config file
$PageIdentifier = "System";

require $_SERVER['DOCUMENT_ROOT'] .'/menu.php';

// now we start an Instance of this class directly, if there had none been started so far..
require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
if (! isset($_SESSION['ObjSystemClass']))
{
	print "<p>Class not in session, we create a new instance<p>";
	$ObjSystemClass = new ClassSystem($PageConfig, $ObjUsers->CurrentEditRightLevel, $PageIdentifier);
}
else
{
	$ObjSystemClass = unserialize(base64_decode($_SESSION['ObjSystemClass']));
}
// We first check on the allpy Button
if (isset($_POST['apply']))
{
	$bIniNeedsToBeWritten = False;
	// OK, we got some changes.. now we have to figure out, what has changed

	foreach ($ObjModules->ArrayAllModules as $Key => $Module)
	{
		if ($Module->ModuleIsAService)
		{
			if (($Module->Enabled) && ! isset($_POST['SEnabled'][$Key])) 
			{	
				// changed from True to False
				//echo "<H2> Enabel $Key changed from True to False</H2>";

				$ObjModules->ini[$Module->ModuleKey]['Enabled'] = False;
				$ObjModules->ArrayAllModules[$Key]->Enabled = False;
				
				$bIniNeedsToBeWritten = True;

			}
			else if((! $Module->Enabled) && isset($_POST['SEnabled'][$Key]))
			{
				//echo "<H2> Enabel $Key changed from False to True</H2>";
				$ObjModules->ini[$Module->ModuleKey]['Enabled'] = True;
				$ObjModules->ArrayAllModules[$Key]->Enabled = True;
				
				$bIniNeedsToBeWritten = True;
			}
			// 2019-12-30
			// Check on number of instances
			if (($Module->RunOnce == False) && isset($_POST['RunInstances'][$Key])) 
			{
		
				$RunInstances = trim($_POST['RunInstances'][$Key]);
				if (($Module->RunInstances) != $RunInstances)
				{
					print ("<p>Old Number of instances: $Module->RunInstances<br>New Number of Instances: $RunInstances<p>");

					$ObjModules->ini[$Module->ModuleKey]['RunInstances'] = $RunInstances;
					$ObjModules->ArrayAllModules[$Key]->RunInstances = $RunInstances;
					$bIniNeedsToBeWritten = True;
				}
			}
		
			// CHeck on timout changed
			// 2019-11-21
			if (($Module->Enabled) && isset($_POST['ModuleControlMaxAge'][$Key])) 
			{
				$ModuleControlMaxAge = trim($_POST['ModuleControlMaxAge'][$Key]);
				if (($Module->ModuleControlMaxAge) != $ModuleControlMaxAge)
				{
					print ("<p>Old Timout: $Module->ModuleControlMaxAge<br>New Timout: $ModuleControlMaxAge<p>");

					$ObjModules->ini[$Module->ModuleKey]['ModuleControlMaxAge'] = $ModuleControlMaxAge;
					$ObjModules->ArrayAllModules[$Key]->ModuleControlMaxAge = $ModuleControlMaxAge;
					$bIniNeedsToBeWritten = True;
				}
			}
		}
	}

	if ($bIniNeedsToBeWritten)
	{

		// Save changes into session
		$_SESSION['ObjModules'] = base64_encode(serialize($ObjModules)); 

		$ObjModules->WriteModulesIniFile();

		
		// 2019-11-21
		// do a restart touch for reloading the multus
		$ObjSystemClass->ScheduleReloadmultusd();
	}

}


/////// 2019-10-31
/////// Now here comes the html stuff and the selction


echo "<table cellspacing='1' cellpadding='3' border=0 bgcolor='#000000'>";
	echo "<tr align=center bgcolor='#FFFFFF'>";
		echo "<th>multus System Services</th>";
	echo "</tr>";
	echo "<tr align=center bgcolor='#FFFFFF'><td>";
		echo "<table cellspacing='1' cellpadding='10' border=0 bgcolor='#000000'></td>";
			echo "<tr align=center bgcolor='#FFFFFF'>";
				echo "<th width='450'>";
					echo "Service";
				echo "</th>";
				echo "<th width='150'>";
					echo "Enabled";
				echo "</th>";
				echo "<th width='150'>";
					echo "Instances";
				echo "</th>";
				echo "<th width='150'>";
					echo "Status";
				echo "</th>";
				echo "<th width='150'>";
					echo "Control Port<br>Watchdog<br>Latency / s";
				echo "</th>";
			echo "</tr>";

			// Now we loop throuch the available modules
			foreach ($ObjModules->ArrayAllModules as $Key => $Module)
			{
				if ($Module->ModuleIsAService)
				{
					echo "<tr align=center bgcolor='#FFFFFF'>";
						echo "<td align=left>";
							echo "$Key $Module->ModuleIdentifier";	
						echo "</td>";
						echo "<td>";
							if ($Module->Enabled)
								echo "<label> <input type='checkbox' name='SEnabled[$Key]' value='True' checked = 'checked'> Enabled </label>";
							else
								echo "<label> <input type='checkbox' name='SEnabled[$Key]' value='True'> Enabled </label>";

						echo "</td>";
						echo "<td>";
							if ($Module->RunOnce)
								echo "<input type='text' size='5' name='RunInstances[$Key]' value='1' disabled>";
							else
								echo "<input type='text' size='5' name='RunInstances[$Key]' value='$Module->RunInstances'>";

						echo "</td>";
						echo "<td>";
							echo $ObjSystemClass->GetRunningStatus($Module); 
						echo "</td>";
						echo "<td>";
							if ($Module->ModuleControlPortEnabled)
							{
								if ($Module->Enabled)
									echo "<input type='text' size='5' name='ModuleControlMaxAge[$Key]' value='$Module->ModuleControlMaxAge'>";
								else
									echo "<input type='text' size='5' name='ModuleControlMaxAge[$Key]' value='$Module->ModuleControlMaxAge' disabled>";
							}

						echo "</td>";
					echo "</tr>";
				}
			}
		echo "</table>";
	echo "</tr>";
	echo "<tr align='right' bgcolor='#FFFFFF'><td alt='center'>";
		echo "<br><p>";
		echo "<input type='submit' name='apply' value='apply changes'>";
		echo "</p>";
	echo "</td></tr>";
echo "</table>";

/////// Put the RebootButton
$ObjModules->PutRebootButtons();

// we store the class data in the session
$_SESSION['ObjSystemClass'] = base64_encode(serialize($ObjSystemClass)); 
require $_SERVER['DOCUMENT_ROOT'] .'/LogoutButton.php';
?>
