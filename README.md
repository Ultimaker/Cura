Cura
====
This is the new, shiny frontend for Cura. Check [daid/LegacyCura](https://github.com/daid/LegacyCura) for the legacy Cura that everyone knows and loves/hates. We re-worked the whole GUI code at Ultimaker, because the old code started to become unmaintainable.

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
If you'd like to contribute a translation of Cura, please first look for [any existing translation](https://github.com/Ultimaker/Cura/tree/master/resources/i18n). If your language is already there in the source code but not in Cura's interface, it may be partially translated.

There are four files that need to be translated for Cura:
1. https://github.com/Ultimaker/Cura/blob/master/resources/i18n/cura.pot
2. https://github.com/Ultimaker/Cura/blob/master/resources/i18n/fdmextruder.def.json.pot
3. https://github.com/Ultimaker/Cura/blob/master/resources/i18n/fdmprinter.def.json.pot (This one is the most work.)
4. https://github.com/Ultimaker/Uranium/blob/master/resources/i18n/uranium.pot

Copy these files and rename them to `*.po` (remove the `t`). Then create the actual translations by filling in the empty `msgstr` entries. These are gettext files, which are plain text so you can open them with any text editor such as Notepad or GEdit, but it is probably easier with a specialised tool such as [POEdit](https://poedit.net/) or [Virtaal](http://virtaal.translatehouse.org/).

Do not hestiate to ask us about a translation or the meaning of some text via Github Issues.

Once the translation is complete, it's probably best to test them in Cura. Use your favourite software to convert the .po file to a .mo file (such as [GetText](https://www.gnu.org/software/gettext/)). Then put the .mo files in the `.../resources/i18n/<language code>/LC_MESSAGES` folder in your Cura installation. Then find your Cura configuration file (next to the log as described above, except on Linux where it is located in `~/.config/cura`) and change the language preference to the name of the folder you just created. Then start Cura. If working correctly, your Cura should now be translated.

To submit your translation, ideally you would make two pull requests where all `*.po` files are located in that same `<language code>` folder in the resources of both the Cura and Uranium repositories. Put `cura.po`, `fdmprinter.def.json.po` and `fdmextruder.def.json.po` in the Cura repository, and put `uranium.po` in the Uranium repository. Then submit the pull requests to Github. For people with less experience with Git, you can also e-mail the translations to the e-mail address listed at the top of the [cura.pot](https://github.com/Ultimaker/Cura/blob/master/resources/i18n/cura.pot) file as the `Report-Msgid-Bugs-To` entry and we'll make sure it gets checked and included.

After the translation is submitted, the Cura maintainers will check for its completeness and check whether it is consistent. We will take special care to look for common mistakes, such as translating mark-up `<message>` code and such. We are often not fluent in every language, so we expect the translator and the international users to make corrections where necessary. Of course, there will always be some mistakes in every translation.

When the next Cura release comes around, some of the texts will have changed and some new texts will have been added. Around the time when the beta is released we will invoke a string freeze, meaning that no developer is allowed to make changes to the texts. Then we will update the translation template `.pot` files and ask all our translators to update their translations. If you are unable to update the translation in time for the actual release, we will remove the language from the drop-down menu in the Preferences window. The translation stays in Cura however, so that someone might pick it up again later and update it with the newest texts. Also, users who had previously selected the language can still continue Cura in their language but English text will appear among the original text.

License
----------------
Cura is released under the terms of the LGPLv3 or higher. A copy of this license should be included with the software.
