<?php 
ob_start (); 

session_name("DWTMultus");
session_start (); 
session_unset (); 
session_destroy (); 

header ("Location: index.php"); 
ob_end_flush (); 

?>
