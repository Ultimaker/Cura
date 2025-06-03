BLACKBELT Cura
====
This is a version of [Ultimaker Cura](https://github.com/ultimaker/cura) customised to support the [BLACKBELT 3D Printer](https://blackbelt-3d.com/) with a slanted gantry.


Logging Issues
------------
For crashes and similar issues, please attach the following information:

* (On Windows) The log as produced by dxdiag (start -> run -> dxdiag -> save output)
* The Cura GUI log file, located at
  * `%APPDATA%\cura\<Cura version>\cura.log` (Windows), or usually `C:\Users\\<your username>\AppData\Roaming\cura\<Cura version>\cura.log`
  * `$USER/Library/Application Support/cura/<Cura version>/cura.log` (OSX)
  * `$USER/.local/share/cura/<Cura version>/cura.log` (Ubuntu/Linux)

If the Cura user interface still starts, you can also reach this directory from the application menu in Help -> Show settings folder

For additional support, you could also ask in the #cura channel on FreeNode IRC. For help with development, there is also the #cura-dev channel.

Dependencies
------------
* [Uranium](https://github.com/Ultimaker/Uranium) Cura is built on top of the Uranium framework.
* [CuraEngine](https://github.com/Ultimaker/CuraEngine) This will be needed at runtime to perform the actual slicing.
* [PySerial](https://github.com/pyserial/pyserial) Only required for USB printing support.
* [python-zeroconf](https://github.com/jstasiak/python-zeroconf) Only required to detect mDNS-enabled printers

Build scripts
-------------
Please checkout [cura-build](https://github.com/Ultimaker/cura-build) for detailed building instructions.

Running from Source
-------------
Please check our [Wiki page](https://github.com/Ultimaker/Cura/wiki/Running-Cura-from-Source) for details about running Cura from source.

Plugins
-------------
Please check our [Wiki page](https://github.com/Ultimaker/Cura/wiki/Plugin-Directory) for details about creating and using plugins.

Supported printers
-------------
Please check our [Wiki page](https://github.com/Ultimaker/Cura/wiki/Adding-new-machine-profiles-to-Cura) for guidelines about adding support for new machines.

Configuring Cura
----------------
Please check out [Wiki page](https://github.com/Ultimaker/Cura/wiki/Cura-Settings) about configuration options for developers.

Translating Cura
----------------
Please check out [Wiki page](https://github.com/Ultimaker/Cura/wiki/Translating-Cura) about how to translate Cura into other languages.

License
----------------
Cura is released under the terms of the LGPLv3 or higher. A copy of this license should be included with the software.
