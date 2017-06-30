Cura
====

This is the new, shiny frontend for Cura. [daid/Cura](https://github.com/daid/Cura.git) is the old legacy Cura that everyone knows and loves/hates.

We re-worked the whole GUI code at Ultimaker, because the old code started to become a unmaintainable.


Logging Issues
------------
Use [this](https://github.com/Ultimaker/Uranium/wiki/Bug-Reporting-Template) template to report issues. New issues that do not adhere to this template will take us a lot longer to handle and will therefore have a lower pirority. 

For crashes and similar issues, please attach the following information:

* (On Windows) The log as produced by dxdiag (start -> run -> dxdiag -> save output)
* The Cura GUI log file, located at
  * %APPDATA%\cura\\`<Cura version>`\cura.log (Windows), or usually C:\Users\\`<your username>`\AppData\Roaming\cura\\`<Cura version>`\cura.log
  * $User/Library/Application Support/cura/`<Cura version>`/cura.log (OSX)
  * $USER/.local/share/cura/`<Cura version>`/cura.log (Ubuntu/Linux)

If the Cura user interface still starts, you can also reach this directory from the application menu in Help -> Show settings folder

Dependencies
------------

* [Uranium](https://github.com/Ultimaker/Uranium)
  Cura is built on top of the Uranium framework.
* [CuraEngine](https://github.com/Ultimaker/CuraEngine)
  This will be needed at runtime to perform the actual slicing.
* [PySerial](https://github.com/pyserial/pyserial)
  Only required for USB printing support.
* [python-zeroconf](https://github.com/jstasiak/python-zeroconf)
  Only required to detect mDNS-enabled printers

Configuring Cura
----------------
* Link your CuraEngine backend by inserting the following line in home/.config/cura/config.cfg :
[backend]
location = /[path_to_the..]/CuraEngine/build/CuraEngine

Build scripts
-------------

Please checkout [cura-build](https://github.com/Ultimaker/cura-build)

Third party plugins
-------------
* [Post Processing Plugin](https://github.com/nallath/PostProcessingPlugin): Allows for post-processing scripts to run on g-code.
* [Barbarian Plugin](https://github.com/nallath/BarbarianPlugin): Simple scale tool for imperial to metric.
* [X3G Writer](https://github.com/Ghostkeeper/X3GWriter): Adds support for exporting X3G files.
* [Auto orientation](https://github.com/nallath/CuraOrientationPlugin): Calculate the optimal orientation for a model.
* [OctoPrint Plugin](https://github.com/fieldofview/OctoPrintPlugin): Send printjobs directly to OctoPrint and monitor their progress in Cura.
* [WirelessPrinting Plugin](https://github.com/probonopd/WirelessPrinting): Print wirelessly from Cura to your 3D printer connected to an ESP8266 module.
* [Electric Print Cost Calculator Plugin](https://github.com/zoff99/ElectricPrintCostCalculator): Calculate the electric costs of a print.

Making profiles for other printers
----------------------------------
There are two ways of doing it. You can either use the generator [here](http://quillford.github.io/CuraProfileMaker/) or you can use [this](https://github.com/Ultimaker/Cura/blob/master/resources/definitions/ultimaker_original.def.json) as a template.

* Change the machine ID to something unique
* Change the machine_name to your printer's name
* If you have a 3D model of your platform you can put it in resources/meshes and put its name under platform
* Set your machine's dimensions with machine_width, machine_depth, and machine_height
* If your printer's origin is in the center of the bed, set machine_center_is_zero to true.
* Set your print head dimensions with the machine_head_shape parameters
* Set the nozzle offset with machine_nozzle_offset_x_1 and machine_nozzle_offset_y1
* Set the start and end gcode in machine_start_gcode and machine_end_gcode
* If your printer has a heated bed, set visible to true under material_bed_temperature

Once you are done, put the profile you have made into resources/definitions, or in definitions in your cura profile folder.
