Submitting bug reports
----------------------
Please submit bug reports for all of Cura and CuraEngine to the [Cura repository](https://github.com/Ultimaker/Cura/issues). There will be a template there to fill in. Depending on the type of issue, we will usually ask for the [Cura log](Logging Issues) or a project file.

If a bug report would contain private information, such as a proprietary 3D model, you may also e-mail us. Ask for contact information in the issue.

Bugs related to supporting certain types of printers can usually not be solved by the Cura maintainers, since we don't have access to every 3D printer model in the world either. We have to rely on external contributors to fix this. If it's something simple and obvious, such as a mistake in the start g-code, then we can directly fix it for you, but e.g. issues with USB cable connectivity are impossible for us to debug.

Requesting features
-------------------
The issue template in the Cura repository does not apply to feature requests. You can ignore it.

When requesting a feature, please describe clearly what you need and why you think this is valuable to users or what problem it solves.

Making pull requests
--------------------
If you want to propose a change to Cura's source code, please create a pull request in the appropriate repository (being [Cura](https://github.com/Ultimaker/Cura), [Uranium](https://github.com/Ultimaker/Uranium), [CuraEngine](https://github.com/Ultimaker/CuraEngine), [fdm_materials](https://github.com/Ultimaker/fdm_materials), [libArcus](https://github.com/Ultimaker/libArcus), [cura-build](https://github.com/Ultimaker/cura-build), [cura-build-environment](https://github.com/Ultimaker/cura-build-environment), [libSavitar](https://github.com/Ultimaker/libSavitar), [libCharon](https://github.com/Ultimaker/libCharon) or [cura-binary-data](https://github.com/Ultimaker/cura-binary-data)) and if your change requires changes on multiple of these repositories, please link them together so that we know to merge them together.

Some of these repositories will have automated tests running when you create a pull request, indicated by green check marks or red crosses in the Github web page. If you see a red cross, that means that a test has failed. If the test doesn't fail on the Master branch but does fail on your branch, that indicates that you've probably made a mistake and you need to do that. Click on the cross for more details, or run the test locally by running `cmake . && ctest --verbose`.