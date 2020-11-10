
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
		<title><?php print $ObjBasicInfos->SiteIdentifier." ".$PageIdentifier; ?> Setup</title>
		<link href="style/dwtmultus.css" rel="stylesheet" type="text/css" />
	</head>

    <body>
		<div class="container">
			<div class="header">
     		   <h2><?php print $ObjBasicInfos->SiteIdentifier." ".$PageIdentifier; ?> Setup</h2>
  			</div><!-- end .header -->
  
			<div class="content">

				<div id="tabsK">
					<ul>
											<!-- CSS Tabs -->
						<?php                              
						// Karl Keusgen
						// 2019-10-27
						// massive changes due to multus III
						//

						// suck in the enabled modules
						require $_SERVER['DOCUMENT_ROOT'] .$ObjBasicInfos->multusModulesClass;
						$ObjModules = unserialize(base64_decode($_SESSION['ObjModules']));

						// initialize the variables
						$PageClass = "";
						$PageConfig = "";
						$PageDescription = "";
						$RunOnce = True;
						$RunInstances = 1;
						$ModulePHPHeadline = "";

						foreach ($ObjModules->ArrayEnabledModules as $Module)
						{
							if ($PageIdentifier == $Module->ModuleIdentifier)
							{
								echo '<li id=current><a href="'.$Module->PHPPage.'"><span>'.$Module->ModulePHPHeadline.'</span></a></li>';

								//we asign the class and the config
								$PageClass = $Module->ModuleClass;
								$PageConfig = $Module->ModuleConfig;
								$PageDescription = $Module->ModuleDescription;
								$RunOnce = $Module->RunOnce;
								$RunInstances = $Module->RunInstances;
								$ModulePHPHeadline = $Module->ModulePHPHeadline;

							}
							else
							{
								echo '<li><a href="'.$Module->PHPPage.'"><span>'.$Module->ModulePHPHeadline.'</span></a></li>';
							}
						}

					echo '</ul>';
				echo '</div>'; // tabsK

				echo "<table cellspacing='5' cellpadding=\"45\"><tr><td>";
					//echo "<h4>$PageDescription</h4>";
					echo "User: $ObjUsers->CurrentUser <br>";
					echo "Edit Rights level: $ObjUsers->CurrentEditRightLevel <br>";

					// put some infos here
					if ($PageClass)
						print "We use this Class: $PageClass <br>";

					if ($PageConfig)
						print "We use this Config: $PageConfig <br>";

					echo "<p>"; 

					if ($RunOnce)
						echo "<form method=post name='FormEreignis' action='".$_SERVER['PHP_SELF']."'>";


?>
