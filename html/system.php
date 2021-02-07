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
			
			// 2021-02-07
			// more parameters to configure by http
			if (($Module->ModuleStatusByPIDFileEnable) && ! isset($_POST['ModuleStatusByPIDFileEnable'][$Key])) 
			{	
				// changed from True to False
				//echo "<H2> Enabel $Key changed from True to False</H2>";

				$ObjModules->ini[$Module->ModuleKey]['ModuleStatusByPIDFileEnable'] = False;
				$ObjModules->ArrayAllModules[$Key]->ModuleStatusByPIDFileEnable = False;
				
				$bIniNeedsToBeWritten = True;

			}
			else if((! $Module->ModuleStatusByPIDFileEnable) && isset($_POST['ModuleStatusByPIDFileEnable'][$Key]))
			{
				//echo "<H2> Enabel $Key changed from False to True</H2>";
				$ObjModules->ini[$Module->ModuleKey]['ModuleStatusByPIDFileEnable'] = True;
				$ObjModules->ArrayAllModules[$Key]->ModuleStatusByPIDFileEnable = True;
				
				$bIniNeedsToBeWritten = True;
			}

			if (($Module->ModuleControlPortEnabled) && ! isset($_POST['ModuleControlPortEnabled'][$Key])) 
			{	
				// changed from True to False
				//echo "<H2> Enabel $Key changed from True to False</H2>";

				$ObjModules->ini[$Module->ModuleKey]['ModuleControlPortEnabled'] = False;
				$ObjModules->ArrayAllModules[$Key]->ModuleControlPortEnabled = False;
				
				$bIniNeedsToBeWritten = True;

			}
			else if((! $Module->ModuleControlPortEnabled) && isset($_POST['ModuleControlPortEnabled'][$Key]))
			{
				//echo "<H2> Enabel $Key changed from False to True</H2>";
				$ObjModules->ini[$Module->ModuleKey]['ModuleControlPortEnabled'] = True;
				$ObjModules->ArrayAllModules[$Key]->ModuleControlPortEnabled = True;
				
				$bIniNeedsToBeWritten = True;
			}

			if (($Module->ModuleControlFileEnabled) && ! isset($_POST['ModuleControlFileEnabled'][$Key])) 
			{	
				// changed from True to False
				//echo "<H2> Enabel $Key changed from True to False</H2>";

				$ObjModules->ini[$Module->ModuleKey]['ModuleControlFileEnabled'] = False;
				$ObjModules->ArrayAllModules[$Key]->ModuleControlFileEnabled = False;
				
				$bIniNeedsToBeWritten = True;

			}
			else if((! $Module->ModuleControlFileEnabled) && isset($_POST['ModuleControlFileEnabled'][$Key]))
			{
				//echo "<H2> Enabel $Key changed from False to True</H2>";
				$ObjModules->ini[$Module->ModuleKey]['ModuleControlFileEnabled'] = True;
				$ObjModules->ArrayAllModules[$Key]->ModuleControlFileEnabled = True;
				
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
			// 2021-02-07
			// Check the kill 0 interval
			if (($Module->Enabled) && isset($_POST['ModuleStatusByPIDFilePeriod'][$Key])) 
			{
				$ModuleStatusByPIDFilePeriod = trim($_POST['ModuleStatusByPIDFilePeriod'][$Key]);
				if (($Module->ModuleStatusByPIDFilePeriod) != $ModuleStatusByPIDFilePeriod)
				{
					print ("<p>Old kill 0 Timout: $Module->ModuleStatusByPIDFilePeriod<br>New kill 0 Timout: $ModuleStatusByPIDFilePeriod<p>");

					$ObjModules->ini[$Module->ModuleKey]['ModuleStatusByPIDFilePeriod'] = $ModuleStatusByPIDFilePeriod;
					$ObjModules->ArrayAllModules[$Key]->ModuleStatusByPIDFilePeriod = $ModuleStatusByPIDFilePeriod;
					$bIniNeedsToBeWritten = True;
				}
			}

			if (($Module->Enabled) && isset($_POST['ModuleControlPort'][$Key])) 
			{
				$ModuleControlPort = trim($_POST['ModuleControlPort'][$Key]);
				if (($Module->ModuleControlPort) != $ModuleControlPort)
				{
					print ("<p>Old TCP Port: $Module->ModuleControlPort<br>New TCP Port: $ModuleControlPort<p>");

					$ObjModules->ini[$Module->ModuleKey]['ModuleControlPort'] = $ModuleControlPort;
					$ObjModules->ArrayAllModules[$Key]->ModuleControlPort= $ModuleControlPort;
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
				echo "<th width='300'>";
					echo "Service";
				echo "</th>";
				echo "<th width='80'>";
					echo "Process Enabled";
				echo "</th>";
				echo "<th width='80'>";
					echo "Kill 0 PID<br><br>Do not disable";
				echo "</th>";
				echo "<th width='80'>";
					echo "Kill 0<br>Interval / s";
				echo "</th>";

				echo "<th width='80'>";
					echo "Control-Port<br><br>Exact Timing";
				echo "</th>";
				echo "<th width='80'>";
					echo "Control<br>TCP-Port";
				echo "</th>";
				echo "<th width='80'>";
					echo "Control-File<br><br>less load<br>+ 1s";
				echo "</th>";
				echo "<th width='80'>";
					echo "Instances";
				echo "</th>";
				echo "<th width='80'>";
					echo "Status";
				echo "</th>";
				echo "<th width='80'>";
					echo "Control Port/File<br>Watchdog<br>Latency / s";
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
							if ($Module->ModuleBinaryStartupDirectlyEnable)
								if ($Module->Enabled)
									if ($Module->ModuleStatusByPIDFileEnable )
										echo "<label> <input type='checkbox' name='ModuleStatusByPIDFileEnable[$Key]' value='True' checked = 'checked'> Enabled </label>";
									else
										echo "<label> <input type='checkbox' name='ModuleStatusByPIDFileEnable[$Key]' value='True'> Enabled </label>";
								else
									if ($Module->ModuleStatusByPIDFileEnable )
										echo "<label> <input type='checkbox' name='ModuleStatusByPIDFileEnable[$Key]' value='True' checked = 'checked' disabled> Enabled </label>";
									else
										echo "<label> <input type='checkbox' name='ModuleStatusByPIDFileEnable[$Key]' value='True' disabled> Enabled </label>";

						echo "</td>";

						echo "<td>";
							if ($Module->ModuleBinaryStartupDirectlyEnable && $Module->ModuleStatusByPIDFileEnable)
							{
								if ($Module->Enabled)
									echo "<input type='text' size='1' name='ModuleStatusByPIDFilePeriod[$Key]' value='$Module->ModuleStatusByPIDFilePeriod'>";
								else
									echo "<input type='text' size='1' name='ModuleStatusByPIDFilePeriod[$Key]' value='$Module->ModuleStatusByPIDFilePeriod' disabled>";
							}

						echo "</td>";
						echo "<td>";
							if ($Module->ModuleBinaryStartupDirectlyEnable)
								if ($Module->Enabled)
									if ($Module->ModuleControlPortEnabled)
										echo "<label> <input type='checkbox' name='ModuleControlPortEnabled[$Key]' value='True' checked = 'checked'> Enabled </label>";
									else
										echo "<label> <input type='checkbox' name='ModuleControlPortEnabled[$Key]' value='True'> Enabled </label>";
								else
									if ($Module->ModuleControlPortEnabled)
										echo "<label> <input type='checkbox' name='ModuleControlPortEnabled[$Key]' value='True' checked = 'checked' disabled> Enabled </label>";
									else
										echo "<label> <input type='checkbox' name='ModuleControlPortEnabled[$Key]' value='True' disabled> Enabled </label>";
									
						echo "</td>";
						echo "<td>";
							if ($Module->ModuleBinaryStartupDirectlyEnable)
								if ($Module->ModuleControlPortEnabled && $Module->Enabled)
									echo "<input type='text' size='1' name='ModuleControlPort[$Key]' value='$Module->ModuleControlPort '>";
								else
									echo "<input type='text' size='1' name='ModuleControlPort[$Key]' value='$Module->ModuleControlPort ' disabled>";

						echo "</td>";
						echo "<td>";
							if ($Module->ModuleBinaryStartupDirectlyEnable)
								if ($Module->Enabled)
									if ($Module->ModuleControlFileEnabled) 
										echo "<label> <input type='checkbox' name='ModuleControlFileEnabled[$Key]' value='True' checked = 'checked'> Enabled </label>";
									else
										echo "<label> <input type='checkbox' name='ModuleControlFileEnabled[$Key]' value='True'> Enabled </label>";
								else
									if ($Module->ModuleControlFileEnabled)
										echo "<label> <input type='checkbox' name='ModuleControlFileEnabled[$Key]' value='True' checked = 'checked' disabled> Enabled </label>";
									else
										echo "<label> <input type='checkbox' name='ModuleControlFileEnabled[$Key]' value='True' disabled> Enabled </label>";

							echo "</td>";

						echo "<td>";
							if ($Module->RunOnce || !$Module->Enabled)
								echo "<input type='text' size='1' name='RunInstances[$Key]' value='$Module->RunInstances' disabled>";
							else
								echo "<input type='text' size='1' name='RunInstances[$Key]' value='$Module->RunInstances'>";

						echo "</td>";

						echo "<td>";
							if ($Module->Enabled)
								echo $ObjSystemClass->GetRunningStatus($Module); 
							else
								echo (" -- "); 
						echo "</td>";
						echo "<td>";
							if ($Module->ModuleBinaryStartupDirectlyEnable && ($Module->ModuleControlPortEnabled || $Module->ModuleControlFileEnabled))
							{
								if ($Module->Enabled)
									echo "<input type='text' size='1' name='ModuleControlMaxAge[$Key]' value='$Module->ModuleControlMaxAge'>";
								else
									echo "<input type='text' size='1' name='ModuleControlMaxAge[$Key]' value='$Module->ModuleControlMaxAge' disabled>";
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
