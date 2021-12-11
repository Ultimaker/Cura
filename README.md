Cura
====
Ultimaker Cura is a state-of-the-art slicer application to prepare your 3D models for printing with a 3D printer. With hundreds of settings and hundreds of community-managed print profiles, Ultimaker Cura is sure to lead your next project to a success.

![Screenshot](cura-logo.PNG)

Logging Issues
------------
For crashes and similar issues, please attach the following information:

* (On Windows) The log as produced by dxdiag (start -> run -> dxdiag -> save output)
* The Cura GUI log file, located at
  * `%APPDATA%\cura\<Cura version>\cura.log` (Windows), or usually `C:\Users\<your username>\AppData\Roaming\cura\<Cura version>\cura.log`
  * `$HOME/Library/Application Support/cura/<Cura version>/cura.log` (OSX)
  * `$HOME/.local/share/cura/<Cura version>/cura.log` (Ubuntu/Linux)

If the Cura user interface still starts, you can also reach this directory from the application menu in Help -> Show settings folder

For additional support, you could also ask in the [#cura channel](https://web.libera.chat/#cura) on [libera.chat](https://libera.chat/). For help with development, there is also the [#cura-dev channel](https://web.libera.chat/#cura-dev).

Dependencies
------------
* [Uranium](https://github.com/Ultimaker/Uranium) Cura is built on top of the Uranium framework.
* [CuraEngine](https://github.com/Ultimaker/CuraEngine) This will be needed at runtime to perform the actual slicing.
* [fdm_materials](https://github.com/Ultimaker/fdm_materials) Required to load a printer that has swappable material profiles.
* [PySerial](https://github.com/pyserial/pyserial) Only required for USB printing support.
* [python-zeroconf](https://github.com/jstasiak/python-zeroconf) Only required to detect mDNS-enabled printers.

For a list of required Python packages, with their recommended version, see `requirements.txt`.

This list is not exhaustive at the moment, please check the links in the next section for more details.

Build scripts
-------------
Please check out [cura-build](https://github.com/Ultimaker/cura-build) for detailed building instructions.

If you want to build the entire environment from scratch before building Cura as well, [cura-build-environment](https://github.com/Ultimaker/cura-build) might be a starting point before cura-build. (Again, see cura-build for more details.)

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
