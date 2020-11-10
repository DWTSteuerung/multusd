<?php 
// Karl Keusgen
// Massive rework for multus III
// Started alredy in 2016

// Session starten
session_name("DWTMultus");
session_start ();

// zuerst ziehen wir uns die Basic Classe wieder rein
require $_SERVER['DOCUMENT_ROOT'] .'/Classes/ClassBasicInfos.php';
$ObjBasicInfos = unserialize(base64_decode($_SESSION['ObjBasicInfos']));

/// Jetzt legen wir die UserKlasse an
require $_SERVER['DOCUMENT_ROOT'] .$ObjBasicInfos->multusUsersClass;
$ObjUsers = new ClassUsers($ObjBasicInfos->multusUsersConfigFile);

// Get the user and pwd from html post
$UserName=$_REQUEST['name'];
$Password=$_REQUEST['pwd'];

// Check validity
$ValidUser = $ObjUsers->CheckPasswort($UserName, $Password);


if ($ValidUser)
{ 
	// Now we store the user information in the Session 
	$_SESSION['ObjUsers'] = base64_encode(serialize($ObjUsers));  
	
	// Now we suck in all available modules
	require $_SERVER['DOCUMENT_ROOT'] .$ObjBasicInfos->multusModulesClass;
	$ObjModules = new ClassModules($ObjBasicInfos->multusModulesConfigFile, $ObjUsers->CurrentEditRightLevel);
	$_SESSION['ObjModules'] = base64_encode(serialize($ObjModules)); 

	### 2019-11-03
	### Now we do something special because of the site name... do a standard class already here..
	## We walk the modules to get the parameter right
	$ModuleToFind = "Site";
	foreach ($ObjModules->ArrayEnabledModules as $Module)
	{
		if ($ModuleToFind == $Module->ModuleIdentifier)
		{
			//we asign the class and the config
			$PageClass = $Module->ModuleClass;
			$PageConfig = $Module->ModuleConfig;
			$PageDescription = $Module->ModuleDescription;

			require $_SERVER['DOCUMENT_ROOT'] .$PageClass;
			$ObjSiteClass = new ClassSite($PageConfig, $ObjUsers->CurrentEditRightLevel, "Setup ".$PageDescription, $ModuleToFind);

			// Now we get the name of the site from the SiteInfo Class..
			foreach ($ObjSiteClass->ini as $Key => $Parameter)
				if ($Key == "SiteName")
				{
					## for th efollowing pages, we update the site identifier and store it again
					$ObjBasicInfos->SiteIdentifier = $Parameter['Value'];
					$_SESSION['ObjBasicInfos'] = base64_encode(serialize($ObjBasicInfos));

					//print ("<h4> OK, we got a new Page name $ObjBasicInfos->SiteIdentifier </h4>");

				}

			## We store this object in the session
			$_SESSION['ObjSite'] = base64_encode(serialize($ObjSiteClass));
		}

		break;
	}
	
	// We start
	header ("Location: internal.php"); 
} 
else 
{ 
  #print "Voll falsch <p>";
  header ("Location: index.php?fehler=1"); 
} 
?> 
