Cura
====

This is the new, shiny frontend for Cura. [daid/Cura](https://github.com/daid/Cura.git) is the old legacy Cura that everyone knows and loves/hates.

We re-worked the whole GUI code at Ultimaker, because the old code started to become a unmaintainable.


Logging Issues
------------
Use [this](https://github.com/Ultimaker/Uranium/wiki/Bug-Reporting-Template) template to report issues. New issues that do not adhere to this template will take us a lot longer to handle and will therefore have a lower pirority. 

For crashes and similar issues, please attach the following information:

* (On Windows) The log as produced by dxdiag (start -> run -> dxdiag -> save output)
* The Cura GUI log file, located at (Windows) $User/AppData/Local/cura/cura.log, (OSX) $User/.cura/cura.log, (Ubuntu) $USER/.local/share/cura
* The Cura Engine log, using Help -> Show Engine Log

Dependencies
------------

* [Uranium](https://github.com/Ultimaker/Uranium)
  Cura is built on top of the Uranium framework.
* [CuraEngine](https://github.com/Ultimaker/CuraEngine)
  This will be needed at runtime to perform the actual slicing.
* [PySerial](https://github.com/pyserial/pyserial)
  Only required for USB printing support.

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
* [Print time calculator](https://github.com/nallath/PrintCostCalculator)
* [Post processing plugin](https://github.com/nallath/PostProcessingPlugin)
* [Barbarian Plugin](https://github.com/nallath/BarbarianPlugin) Simple scale tool for imperial to metric.

Making profiles for other printers
----------------------------------
There are two ways of doing it. You can either use the generator [here](http://quillford.github.io/CuraProfileMaker/) or you can use [this](https://github.com/Ultimaker/Cura/blob/master/resources/settings/ultimaker_original.json) as a template.

* Change the machine ID to something unique
* Change the machine_name to your printer's name
* If you have a 3D model of your platform you can put it in resources/meshes and put its name under platform
* Set your machine's dimensions with machine_width, machine_depth, and machine_height
* If your printer's origin is in the center of the bed, set machine_center_is_zero to true.
* Set your print head dimensions with the machine_head_shape parameters
* Set the nozzle offset with machine_nozzle_offset_x_1 and machine_nozzle_offset_y1
* Set the start and end gcode in machine_start_gcode and machine_end_gcode
* If your printer has a heated bed, set visible to true under material_bed_temperature

Once you are done, put the profile you have made into resources/settings.
