
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
<br>

![Logo]

# Ultimaker Cura

*State-of-the-art slicer app to prepare* <br>
*your 3D models for your 3D printer.*

*With hundreds of settings & community-managed print profiles,* <br>
*Ultimaker Cura is sure to lead your next project to a success.*

<br>
<br>

[![Button Building]][Building]   
[![Button Plugins]][Plugins]   
[![Button Machines]][Machines]

[![Button Settings]][Settings]   
[![Button Localize]][Localize]

<br>
<br>

![Showcase]

</div>

<br>
<br>

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
[Logo]: resources/images/cura-icon.png
[#]: #


<!---------------------------------[ Badges ]---------------------------------->

[Badge Contributors]: https://img.shields.io/github/contributors/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=e2467d&color=a2325b&logo=GitHub
[Badge PullRequests]: https://img.shields.io/github/issues-pr/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=yellow&color=a68311&logo=GitExtensions
[Badge License]: https://img.shields.io/badge/License-LGPL3-015d93.svg?style=for-the-badge&labelColor=blue&logoColor=white&logo=GNU
[Badge Closed]: https://img.shields.io/github/issues-closed/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=569A31&color=457a27&logo=AddThis
[Badge Issues]: https://img.shields.io/github/issues/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=C9284D&color=931d39&logo=AdBlock
[Badge Conan]: https://img.shields.io/github/workflow/status/Ultimaker/Cura/conan-package?style=for-the-badge&logoColor=white&labelColor=EF443B&color=aa302a&logo=Conan&label=Conan%20Package
[Badge Test]: https://img.shields.io/github/workflow/status/Ultimaker/Cura/unit-test?style=for-the-badge&logoColor=white&labelColor=00979D&color=007175&logo=Codacy&label=Unit%20Test
[Badge Size]: https://img.shields.io/github/repo-size/ultimaker/cura?style=for-the-badge&logoColor=white&labelColor=66459B&color=50377a&logo=GoogleAnalytics


<!---------------------------------[ Buttons ]--------------------------------->

[Button Localize]: https://img.shields.io/badge/Help_Localize-e2467d?style=for-the-badge&logoColor=white&logo=GoogleTranslate
[Button Machines]: https://img.shields.io/badge/Adding_Machines-yellow?style=for-the-badge&logoColor=white&logo=CloudFoundry
[Button Settings]: https://img.shields.io/badge/Configuration-00979D?style=for-the-badge&logoColor=white&logo=CodeReview
[Button Building]: https://img.shields.io/badge/Building_Cura-blue?style=for-the-badge&logoColor=white&logo=GitBook
[Button Plugins]: https://img.shields.io/badge/Plugin_Usage-569A31?style=for-the-badge&logoColor=white&logo=ROS


