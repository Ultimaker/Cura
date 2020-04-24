Repositories
====
Cura uses a number of repositories where parts of our source code are separated, in order to get a cleaner architecture. Those repositories are:
* [Cura](https://github.com/Ultimaker/Cura), the main repository for the front-end of Cura. This contains all of the business logic for the front-end, including the specific types of profiles that are available, the concept of 3D printers and materials, specific tools for handling 3D printed models, pretty much all of the GUI, as well as Ultimaker services such as the Marketplace and accounts.
* The Cura repository is built on [Uranium](https://github.com/Ultimaker/Uranium), a framework for desktop applications that handle 3D models and have a separate back-end. This provides Cura with a basic GUI framework ([Qt](https://www.qt.io/)), a 3D scene, a rendering system, a plug-in system and a system for stacked profiles that change settings.
* In order to slice, Cura starts [CuraEngine](https://github.com/Ultimaker/CuraEngine) in the background. This does the actual process that converts 3D models into a toolpath for the printer.
* Communication to CuraEngine goes via [libArcus](https://github.com/Ultimaker/libArcus), a small library that wraps around [Protobuf](https://developers.google.com/protocol-buffers/) in order to make it run over a local socket.
* Cura's build scripts are in [cura-build](https://github.com/Ultimaker/cura-build) and build scripts for building dependencies are in [cura-build-environment](https://github.com/Ultimaker/cura-build-environment).

There are also a number of repositories under our control that are not integral parts of Cura's architecture, but more like separated side-gigs:
* Loading and writing 3MF files is done through [libSavitar](https://github.com/Ultimaker/libSavitar).
* Loading and writing UFP files is done through [libCharon](https://github.com/Ultimaker/libCharon).
* To make the build system a bit simpler, some parts are pre-compiled in [cura-binary-data](https://github.com/Ultimaker/cura-binary-data). This holds things like the machine-readable translation files and the Marlin builds for firmware updates, which would require considerable tooling to build automatically.
* There are automated GUI tests in [Cura-squish-tests](https://github.com/Ultimaker/Cura-squish-tests).
* Material profiles are stored in [fdm_materials](https://github.com/Ultimaker/fdm_materials). This is separated out and combined in our build process, so that the firmware for Ultimaker's printers can use the same set of profiles too.