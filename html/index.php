<?php 

## Karl Keusgen
## Massive Rework for multus III
## 2019-10-26
session_name("DWTMultus");
session_start (); 

require $_SERVER['DOCUMENT_ROOT'] .'/Classes/ClassBasicInfos.php';
$ObjBasicInfos = new ClassBasicInfos();

$_SESSION['ObjBasicInfos'] = base64_encode(serialize($ObjBasicInfos));

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
		<!-- <meta http-equiv=”refresh” content="90" /> -->
		<title>Site: <?php echo $ObjBasicInfos->SiteIdentifier ?> Login </title>
		<link href="style/dwtmultus.css" rel="stylesheet" type="text/css" />
	</head>

	<body>

		<div class="container">
			<div class="header">
				<h1>Welcome</h1>
		 	</div>
			<div class="content">
				<form action="login.php" method="post"> 
					<table border="0" align="center" cellpadding="4" >

						<tr><td></td></tr>
						<tr><td><h1> Site: <?php echo $ObjBasicInfos->SiteIdentifier ?></h1></td></tr>

						<?php 
						if (isset ($_REQUEST["fehler"])) 
						{ 
							echo "<tr><th><F1>";
							echo "Die Zugangsdaten waren ungültig."; 
							echo "</F1></th></tr>";
						} 
						?>

						<p></p>

						<tr><td>

						<table border="0" align="center" cellpadding="4"> 
							<tr><td width="250"><b>multus III login</b></td><td width="250"></td></tr>
							<tr>
								<td><strong>User:</strong></td><td> <input type="text" name="name" size="20"></td>
							</tr>
							<tr>
								<td><strong>Password:</strong></td><td> <input type="password" name="pwd" size="20"></td> 
							</tr>
							<tr>
								<td></td><td colspan="2" align="left"><input type="submit" value="Login"></td>
							</tr>
							<tr>
								
								<td><a href="logs/index.php" target="_blank">System logs</a> </td><td></td>
							</tr>
						</table>

						</td></tr>
					</table>
				</form> 
				<p>
			</div> <!-- end .content --> 
				
			<div class="footer">
				<p><a href="http://www.deutsche-windtechnik.com/onshore-steuerungselektronik.html" target="_blank"><img src="img/DWAG_MZ_Standard_PNG.png" width="164" height="60" align="right" /></a></p>
			</div> <!-- end .footer -->
		</div> <!-- end .container -->
	</body>
</html>
