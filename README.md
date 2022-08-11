
<br>

<div align = center>

[![Badge Issues]][Issues]   
[![Badge PullRequests]][PullRequests]   
[![Badge Closed]][Closed]

[![Badge Size]][#]   
[![Badge License]][License]   
[![Badge Contributors]][Contributors]

[![Badge Test]][Test]   
[![Badge Conan]][Conan]   

<br>

# Cura

Ultimaker Cura is a state-of-the-art slicer application to prepare your 3D models for printing with a 3D printer. With hundreds of settings
and hundreds of community-managed print profiles, Ultimaker Cura is sure to lead your next project to a success.

![Showcase]

## Logging Issues

For crashes and similar issues, please attach the following information:

* (On Windows) The log as produced by dxdiag (start -> run -> dxdiag -> save output)
* The Cura GUI log file, located at
    * `%APPDATA%\cura\<Cura version>\cura.log` (Windows), or usually `C:\Users\<your username>\AppData\Roaming\cura\<Cura version>\cura.log`
    * `$HOME/Library/Application Support/cura/<Cura version>/cura.log` (OSX)
    * `$HOME/.local/share/cura/<Cura version>/cura.log` (Ubuntu/Linux)

If the Cura user interface still starts, you can also reach this directory from the application menu in Help -> Show settings folder.
An alternative is to install the [ExtensiveSupportLogging Plugin]
this creates a zip folder of the relevant log files. If you're experiencing performance issues, we might ask you to connect the CPU profiler
in this plugin and attach the collected data to your support ticket. 

## Running from Source
Please check our [Wiki page][Building] for details about running Cura from source.

## Plugins
Please check our [Wiki page][Plugins] for details about creating and using plugins.

## Supported printers
Please check our [Wiki page][Machines] for guidelines about adding support
for new machines.

## Configuring Cura
Please check out [Wiki page][Settings] about configuration options for developers.

## Translating Cura
Please check out [Wiki page][Localize] about how to translate Cura into other languages.

## License
![Badge License] 
Cura is released under terms of the LGPLv3 or higher. A copy of this license should be included with the software. Terms of the license can be found in the LICENSE file. Or at
http://www.gnu.org/licenses/lgpl.html

> But in general it boils down to:  
> **You need to share the source of any Cura modifications**

</div>

<br>


<!----------------------------------------------------------------------------->

[ExtensiveSupportLogging Plugin]: https://marketplace.ultimaker.com/app/cura/plugins/UltimakerPackages/ExtensiveSupportLogging
[Contributors]: https://github.com/Ultimaker/Cura/graphs/contributors
[PullRequests]: https://github.com/Ultimaker/Cura/pulls
[Machines]: https://github.com/Ultimaker/Cura/wiki/Adding-new-machine-profiles-to-Cura
[Building]: https://github.com/Ultimaker/Cura/wiki/Running-Cura-from-Source
[Localize]: https://github.com/Ultimaker/Cura/wiki/Translating-Cura
[Settings]: https://github.com/Ultimaker/Cura/wiki/Cura-Settings
[Plugins]: https://github.com/Ultimaker/Cura/wiki/Plugin-Directory
[Closed]: https://github.com/Ultimaker/Cura/issues?q=is%3Aissue+is%3Aclosed
[Issues]: https://github.com/Ultimaker/Cura/issues
[Conan]: https://github.com/Ultimaker/Cura/actions/workflows/conan-package.yml
[Test]: https://github.com/Ultimaker/Cura/actions/workflows/unit-test.yml

[Showcase]: cura-logo.PNG
[License]: LICENSE
[#]: #


<!---------------------------------[ Badges ]---------------------------------->

[Badge Contributors]: https://img.shields.io/github/contributors/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=e2467d&color=b43863&logo=
[Badge PullRequests]: https://img.shields.io/github/issues-pr/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=yellow&color=bc9513&logo=
[Badge License]: https://img.shields.io/badge/License-LGPL3-015d93.svg?style=for-the-badge&labelColor=blue&logoColor=white&logo=GNU
[Badge Closed]: https://img.shields.io/github/issues-closed/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=569A31&color=457a27&logo=
[Badge Issues]: https://img.shields.io/github/issues/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=C9284D&color=931d39&logo=
[Badge Conan]: https://img.shields.io/github/workflow/status/Ultimaker/Cura/conan-package?style=for-the-badge&logoColor=white&labelColor=EF443B&color=bf362f&logo=&label=Conan%20Package
[Badge Test]: https://img.shields.io/github/workflow/status/Ultimaker/Cura/unit-test?style=for-the-badge&logoColor=white&labelColor=00979D&color=007a7e&logo=&label=Unit%20Test
[Badge Size]: https://img.shields.io/github/repo-size/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=66459B&color=50377a&logo=


