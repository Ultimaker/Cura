Cura
====

This is the new, shiny frontend for Cura. [daid/Cura](https://github.com/daid/Cura.git) is the old legacy Cura that everyone knows and loves/hates.

We re-worked the whole GUI code at Ultimaker, because the old code started to become a unmaintainable.

Dependencies
------------

* [Uranium](https://github.com/Ultimaker/Uranium)
  Cura is built on top of the Uranium framework.
* [CuraEngine](https://github.com/Ultimaker/CuraEngine)
  This will be needed at runtime to perform the actual slicing.
* PySerial
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
[Print time calculator](https://github.com/nallath/PrintCostCalculator)

Making profiles for other printers
----------------------------------
Fill in the settings about your printer [here](http://quillford.github.io/CuraProfileMaker/).

Once you are done, put the profile you have made into resources/settings.
