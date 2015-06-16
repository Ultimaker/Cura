Cura
====

This is the new, shiny, unreleased frontend for Cura. [daid/Cura](https://github.com/daid/Cura.git) is the old legacy Cura that everyone knows and loves/hates.

We re-worked the whole GUI code at Ultimaker, because my old code started to become an unmaintainable ball of poo.

Dependencies
------------

* Uranium
  Cura is built on top of the Uranium framework.
* CuraEngine
  This will be needed at runtime to perform the actual slicing.
* PySerial
  Only required for USB printing support.

Build scripts
-------------

Please checkout [cura-build](https://github.com/Ultimaker/cura-build)
