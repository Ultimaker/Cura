Repositories
====
Cura uses a number of repositories where parts of our source code are separated, in order to get a cleaner architecture. Those repositories are:
* [Cura](https://github.com/Ultimaker/Cura) is the main repository for the front-end of Cura. This contains:
    - all of the business logic for the front-end, including the specific types of profiles that are available
    -  the concept of 3D printers and materials
    -  specific tools for handling 3D printed models
    -  pretty much all of the GUI
    -  Ultimaker services such as the Marketplace and accounts.
* [Uranium](https://github.com/Ultimaker/Uranium) the underlying framework the Cura repository is built on. [Uranium](https://github.com/Ultimaker/Uranium) is a framework for desktop applications that handle 3D models and have a separate back-end. This provides Cura with:
    - a basic GUI framework ([Qt](https://www.qt.io/))
    - a 3D scene, a rendering system
    - a plug-in system
    - a system for stacked profiles that change settings.
*  [CuraEngine](https://github.com/Ultimaker/CuraEngine) the slicer used by Cura in the background. This does the actual process that converts 3D models into a toolpath for the printer.
* [libArcus](https://github.com/Ultimaker/libArcus) handles the communication to CuraEngine. [libArcus](https://github.com/Ultimaker/libArcus) is a small library that wraps around [Protobuf](https://developers.google.com/protocol-buffers/) in order to make it run over a local socket.
* [cura-build](https://github.com/Ultimaker/cura-build): Cura's build scripts.  
* [cura-build-environment](https://github.com/Ultimaker/cura-build-environment) build scripts for building dependencies.

There are also a number of repositories under our control that are not integral parts of Cura's architecture, but more like separated side-gigs:
* [libSavitar](https://github.com/Ultimaker/libSavitar) is used for loading and writing 3MF files.
* [libCharon](https://github.com/Ultimaker/libCharon) is used for loading and writing UFP files.
*  [cura-binary-data](https://github.com/Ultimaker/cura-binary-data) pre-compiled parts to make the build system a bit simpler. This holds things which would require considerable tooling to build automatically like:
    - the machine-readable translation files
    - the Marlin builds for firmware updates
* [Cura-squish-tests](https://github.com/Ultimaker/Cura-squish-tests): automated GUI tests.
* [fdm_materials](https://github.com/Ultimaker/fdm_materials) stores Material profiles. This is separated out and combined in our build process, so that the firmware for Ultimaker's printers can use the same set of profiles too.

Interplay
----
At a very high level, Cura's repositories interconnect as follows:

![Overview of interplay between repositories](resources/repositories.svg)
